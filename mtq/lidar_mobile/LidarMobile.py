# Importer les objects du module core de QGIS 
import os
from qgis.core import (QgsVectorLayer, QgsRectangle, QgsSpatialIndex, QgsCoordinateReferenceSystem)
from typing import Union, Dict

from ..functions.reprojections import reprojectPoints
from .IndexLidar import IndexLidar
from .Lidar import Lidar

class LidarMobile:
    """
    Module qui permet de faire la gestion des index et nuages de point du lidar mobile.
    Le module contient les références vers les indexes de téléchargement et les nuage de points.
    """

    def __init__(self, layer_index:QgsVectorLayer):
        # Set les valeurs des indexs vides
        self.reset()
        # Mettre à jour l'index à partir de la couche
        self.updateIndex(layer_index)

    def __repr__ (self): return f"LidarMobile ({len(self)} indexs)"

    def __len__(self): return len(self.dict_index)

    def __iter__ (self): return self.dict_index.__iter__()

    def __getitem__(self, key): 
        try: return self.dict_index[key]
        except: raise KeyError(f"L'index lidar ({key}) n'existe pas")

    def __contains__(self, key): return key in self.dict_index

    def reset(self):
        """ Permet de reset toutes les indexs vides """
        self.dict_index:Dict[str, IndexLidar] = {}
        self.dict_index_id: Dict[int, str] = {}
        self.dict_lidar:Dict[str, Lidar] = {}
        self.crs = QgsCoordinateReferenceSystem()

    def isEmpty(self): 
        """
        Permet de vérifier si le module est vide

        Returns (bool): True si le module est vide, False sinon
        """
        return len(self.dict_index) == 0

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

    def set_output_folder(self, folder:str):
        """
        Permet de définir le dossier de sortie pour les fichiers lidar

        Args:
            folder (str): Le chemin vers le dossier de sortie
        """
        for index in self.listIndex(): index.set_folder(folder)
        self.updateLidar(folder)

    def listIndex(self): return list(self.dict_index.values())

    def updateIndex(self, layer_index:QgsVectorLayer, **kwargs):
        """
        Mettre à jour les indexs lidar à partir d'un couche.

        Args:
            layer_index (QgsVectorLayer): La couche qui contient les index lidar à utiliser

        kwargs:
            champ_lidar_id (str): Le nom du champs qui contient l'indentifiant de la run lidar
            champ_lidar_date (str): Le nom du champs qui contient la date de la run lidar
            champ_lidar_telechargement (str): Le nom du champs qui contient le lien de téléchargement de la run lidar
        """
        if not layer_index: return False
        self.crs = layer_index.crs()
        # Index spatial des géometries des index
        self.spatial_index = QgsSpatialIndex(layer_index.getFeatures())
        # Parcourir toutes les entités de la couche d'index
        for feat_index in layer_index.getFeatures():
            # Créer l'objet IndexLidar pour la trajectoire
            index = IndexLidar.fromFeat(feat_index, self.crs, **kwargs)
            # Ajouter l'objet IndexLidar au dictionnaire
            self.dict_index[index.id()] = index
            self.dict_index_id[feat_index.id()] = index.id()
        return True

    def updateLidar(self, folder):
        for index in self.listIndex():
            if os.path.samefile(index.folder(), folder):
                self.addLidar(index)
    
    def clip(self, id_index:str, layer_poly:QgsVectorLayer, output="", sufix="_clip"):
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
        if output == "": output = index.createFile(sufix)
        # Découper le fichier
        return lidar.clip(output, layer_poly)
    
    def merge(self, list_index:list[str], output:str, **kwargs):
        """
        Permet de fusionner plusieurs nuages de points en un seul

        Args:
            list_index (list[str]): La liste des index à fusionner
            output (str, optional): Le nom du fichier en sortie. Defaults to génération automatique.

        Returns (Lidar): L'objet Lidar du nuage de point généré
        """
        # Vérifier si la liste d'index est vide
        if not list_index: return False
        list_lidar = []
        for id_index in list_index:
            # Définir la référence de l'index du lidar a découper
            if not self.get(id_index): return False
            # Vérifier si le lidar est téléchargé
            lidar = self.getLidar(id_index)
            # Sinon télécharger le fichier
            if not lidar: lidar = self.download(id_index)
            list_lidar.append(lidar.file())
        
        return Lidar.merge_lidar(list_lidar, output, **kwargs)

    def applatir(self, id_index:str, output="", sufix="_applatit"):
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
        if output == "": output = index.createFile(sufix)
        return lidar.applatir(output, points_z)
        
    
        