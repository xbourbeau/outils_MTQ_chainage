# Importer les objects du module core de QGIS 
import os
from qgis.core import (QgsGeometry, QgsPointXY, QgsVectorLayer, QgsField, QgsRectangle,
                        QgsCoordinateReferenceSystem, QgsSpatialIndex, QgsFeature, QgsWkbTypes, QgsFeatureIterator)
from typing import Union, Dict
import numpy as np

from ..fnt.reprojections import reprojectPoints
from .IndexLidar import IndexLidar
from .Lidar import Lidar

class LidarMobile:
    """
    Module qui permet de faire la gestion des index et nuages de point du lidar mobile.
    Le module contient les références vers les indexes de téléchargement et les nuage de points.
    """

    def __init__(self, feats_index:QgsFeatureIterator, crs:QgsCoordinateReferenceSystem):
        self.dict_index:Dict[str, IndexLidar] = {}
        self.dict_index_id: Dict[int, str] = {}
        self.dict_lidar:Dict[str, Lidar] = {}

        self.updateIndex(feats_index, crs)

    @classmethod
    def fromLayer(cls, layer_index:QgsVectorLayer):
        return cls(layer_index.getFeatures(), layer_index.crs())

    def __repr__ (self): return f"LidarMobile ({len(self)} indexs)"

    def __len__(self): return len(self.dict_index)

    def __iter__ (self): return self.dict_index.__iter__()

    def __getitem__(self, key): 
        try: return self.dict_index[key]
        except: raise KeyError(f"L'index lidar ({key}) n'existe pas")

    def __contains__(self, key): return key in self.dict_index

    def addLidar(self, index:IndexLidar):
        """
        Perment d'ajoute une référence d'index au dictionnaire

        Args:
            index (IndexLidar): L'index à ajouter
        """
        self.dict_lidar[index.id()] = Lidar.fromIndex(index)

    def download(self, id_index, file_path="") -> Lidar:
        """
        Permet de télécharger un nuage de points à partir de index spécifier 

        Args:
            id_index (str): L'indentifiant de l'index à télécharger
            file_path (str, optional): Spécifier un chemin ou enregistrer le fichier. Defaults to "".

        Returns (Lidar): L'objet Lidar associé au nuage de point 
        """
        # Définir la référence de l'index du nuage de point
        index = self.get(id_index)
        if not index: return False
        # Télécharger le nuage de points associé à l'index
        if not index.download(file_path): return False
        # Ajouter le nuage de points à la référence du module
        self.addLidar(index)
        # Retourner la référence du nuage de point
        return self.getLidar(id_index)

    def get(self, index:str):
        return self.dict_index.get(index, None)
    
    def getIndexById(self, id):
        return self.get(self.dict_index_id.get(id))

    def getLidar(self, index:str):
        return self.dict_lidar.get(index, None)

    def getCrs(self):
        """ Retourne le CRS courrant de l'object """
        return self.crs
    
    def getIndexFromYear(self, year:int):
        """ Permet de retourner les indexs par année du relevée """
        return [index for index in self.listIndex() if index.year() == year]

    def getIndexInExtent(self, extent:QgsRectangle) -> list[IndexLidar]:
        """
        Permet de retourner une liste d'IndexLidar dont la géometrie intersecte
        l'étendu spécifiée.

        Args:
            extent (QgsRectangle): L'étendu à utiliser

        Returns (list of IndexLidar): La liste des index lidar qui se trouve dans l'étendu
        """
        indexs = []
        # Parcourir les id des index qui intersect l'étendu
        for id in self.spatial_index.intersects(extent):
            # Définir l'index à partir de l'id du QgsFeature
            index = self.getIndexById(id)
            # Vérifier la vrai intersection et ajouter l'index à la liste
            if index.geometry().intersects(extent): indexs.append(index)
        return indexs

    def listIndex(self): return list(self.dict_index.values())

    def updateIndex(self, feats_index:QgsFeatureIterator, crs:QgsCoordinateReferenceSystem):
        self.crs = crs
        # Index spatial des géometries des index
        self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        # Parcourir toutes les entités de la couche d'index
        for feat_index in feats_index:
            # Ajouter la trajectoire à l'index spatial
            self.spatial_index.addFeature(feat_index)
            # Créer l'objet IndexLidar pour la trajectoire
            index = IndexLidar.fromFeat(feat_index, crs)
            # Ajouter l'objet IndexLidar au dictionnaire
            self.dict_index[index.id()] = index
            self.dict_index_id[feat_index.id()] = index.id()

    def updateLidar(self, folder):
        for index in self.listIndex():
            if os.path.samefile(index.folder(), folder):
                self.addLidar(index)
    
    def clip(self, id_index:str, layer_poly:QgsVectorLayer, output=""):
        """
        Permet de découper un nuage de point selon une couche de polygone

        Args:
            id_index (str): Le numéro de l'index du lidar à découper
            layer_poly (QgsVectorLayer): La couche de polygone à utiliser pour le découpage
            output (str, optional): Le nom du fichier en sortie. Defaults to génération automatique.

        Returns (Lidar): L'objet Lidar du nuage de point généré
        """
        # Définir la référence de l'index du lidar a découper
        index = self.get(id_index)
        if not index: return False
        # Vérifier si le lidar est téléchargé
        lidar = self.getLidar(index)
        # Sinon télécharger le fichier
        if not lidar: lidar = self.download(id_index)
        # Créer un nom si aucun est défini
        if output == "": output = index.createFile("_clip")
        # Découper le fichier
        return lidar.clip(output, layer_poly)

    def applatir(self, id_index:str, output=""):
        """
        Permet de découper un nuage de point selon une couche de polygone

        Args:
            id_index (str): Le numéro de l'index du lidar à applatir
            output (str, optional): Le nom du fichier en sortie. Defaults to génération automatique.

        Returns (Lidar): L'objet Lidar du nuage de point généré
        """
        # Définir la référence de l'index du lidar a découper
        index = self.get(id_index)
        if not index: return False
        # Vérifier si le lidar est téléchargé
        lidar = self.getLidar(index)
        # Sinon télécharger le fichier
        if not lidar: lidar = self.download(id_index)
        # Définir la liste des points qui constitue la trajectoire du lidar
        points = index.getTrajectoryCoords()
        # Reprojecter les points dans le même CRS que le lidar
        points = reprojectPoints(points, self.getCrs(), lidar.crs())
        # Ajouter les Z au coordonnée de la ligne
        points_z = lidar.fitLine(points, 0,5, classifications=[2])
        # Créer un nom si aucun est défini
        if output == "": output = index.createFile("_applatit")
        return lidar.applatir(output, points_z)
        
