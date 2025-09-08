import os
import numpy as np
from osgeo import gdal
import pandas as pd

from qgis.core import (QgsSpatialIndex, QgsFeatureIterator, QgsCoordinateReferenceSystem,
                       QgsFeature, QgsVectorLayer, QgsField, QgsPointXY, QgsGeometry,
                       QgsVectorLayerUtils)
from typing import Union, Dict
from PyQt5.QtCore import QVariant

from ..geomapping.RTSS import RTSS
from ..geomapping.Geocodage import FeatRTSS
from ..geomapping.Chainage import Chainage

from ..functions.reprojections import reprojectPoint

from .VoieDevers import VoieDevers


class AnalyseDevers:

    def __init__(self):
        # Indicateur de si l'objet a créer les index pour la couches BGR - Voies
        self._has_bgr_surfacique_index = False
        # Le CRS à utiliser
        self._crs:QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem()
        # Interval des chainage à utiliser par défault pour l'analyse
        self.interval_chainage = 10
        # Offset pour la recherche de voie à utiliser par défault pour l'analyse
        self.initial_offset = 10
        
        # Nom des champs de la couche de BGR - Voie pour les infomations à vérifier
        self.field_rtss_voie = "numrtss"
        self.field_chainage_debut_voie = "chdebut"
        self.field_chainage_fin_voie = "chfin"
        self.field_code_voie = "codvoie"

        # Définir les paramètres par défault de l'analyse
        self.reset()

    def set_layer_bgr_surfacique(self, voie_features, crs:QgsCoordinateReferenceSystem, **kwargs):
        """
        Permet de créer les index des voie à partir d'une couche de voie BGR.

        Args:
            voie_features (itérateur features): Les features à parcourir pour les voies BGR
            crs (QgsCoordinateReferenceSystem): Le système de coordonnée des features
        
        kwargs:
            field_rtss_voie: le nom du champs de la couche avec le RTSS. Defaults to "numrtss"
            field_chainage_debut_voie: le nom du champs de la couche avec le chainage de début. Defaults to "chdebut"
            field_chainage_fin_voie: le nom du champs de la couche avec le chainage de fin. Defaults to "chfin"
            field_code_voie: le nom du champs de la couche avec le code de voie. Defaults to "codvoie"
        """
        # Vérifier si cette étape à déjà été faite
        if self.current_step() != 0: raise Exception("L'index BGR surfacique a déjà été créé.")
        # Définir le CRS de l'analyse
        self._crs = QgsCoordinateReferenceSystem(crs)
        # Créer l'index spatial des voies de BGR
        self._voie_spatial_index = QgsSpatialIndex()
        # Créer l'index des features des voies de BGR
        self._voie_index:Dict[int, QgsFeature] = {}
        # Définir les champs de la chouche à utiliser s'il sont défini
        if "field_rtss_voie" in kwargs: self.field_rtss_voie = kwargs["field_rtss_voie"]
        if "field_chainage_debut_voie" in kwargs: self.field_chainage_debut_voie = kwargs["field_chainage_debut_voie"]
        if "field_chainage_fin_voie" in kwargs: self.field_chainage_fin_voie = kwargs["field_chainage_fin_voie"]
        if "field_code_voie" in kwargs: self.field_code_voie = kwargs["field_code_voie"]
        
        # Parcourir les featrures des voies 
        for feat in voie_features:
            # Skip si la voie n'est pas une voie pricipale
            if not feat[self.field_code_voie][1:2] in ('P'): continue
            # Ajouter le feature à l'index spatial
            self._voie_spatial_index.addFeature(feat)
            # Ajouter le feature à l'index des features
            self._voie_index[feat.id()] = feat
        # Indiquer que les indexs de la couche sont défini
        self._has_bgr_surfacique_index = True

    def current_step(self):
        """ Permet de retourner qu'elle étape de l'analyse a été fait"""
        # Étape 1: Index de la couche BGR - Voies
        if not self._has_bgr_surfacique_index: return 0
        # Étape 2: Calculer les devers
        if not self._has_devers: return 1
        # Étape 3: Analyser les devers
        if not self._has_analyse: return 2
        # Traitement complété
        else: return 3

    def crs(self): return self._crs

    def reset(self, reset_all=False):
        """
        Permet de reset les étapes d'analyse, sauf l'indexation des voies bgr par défault.
        
        Args:
            reset_all(bool): Permet de reset également l'indexation des voies bgr
        """
        # Index des Voie de devers par chainage
        self._index_devers:Dict[int, list[VoieDevers]] = {}
        # FeatRTSS à utiliser pour l'analyse
        self.feat_rtss:FeatRTSS = None
        # Limite de chainage du FeatRTSS
        self.limit_chainage_d = None
        self.limit_chainage_f = None
        # Indicateur sur la progression des étapes
        self._has_devers = False
        self._has_analyse = False

        # Reset les infos de l'indexation des voies bgr
        if reset_all:
            # Définir le CRS de l'analyse
            self._crs = QgsCoordinateReferenceSystem()
            # Créer l'index spatial des voies de BGR
            self._voie_spatial_index = QgsSpatialIndex()
            # Créer l'index des features des voies de BGR
            self._voie_index:Dict[int, QgsFeature] = {}
            self._has_bgr_surfacique_index = False

    def set_feat_rtss(self, feat_rtss:FeatRTSS): self.feat_rtss = feat_rtss

    def set_limite_chainage(self, chainage_d:Union[int, Chainage]=None, chainage_f:Union[int, Chainage]=None):
        if self.feat_rtss is None and (chainage_d is None or chainage_f is None):
            raise Exception("Veuillez définir un feat_rtss!")
        
        if chainage_d is None: self.limit_chainage_d = self.feat_rtss.chainageDebut()
        else: self.limit_chainage_d = Chainage(chainage_d)

        if chainage_f is None: self.limit_chainage_f = self.feat_rtss.chainageFin()
        else: self.limit_chainage_f = Chainage(chainage_f)

    def creer_devers(self, **kwargs):
        """
        Permet de créer les VoiesDevers selon les voie bgr pour la section RTSS (cd-cf) défini. 

        kwargs:
            feat_rtss: Spécifier un FeatRTSS
            chainage_d: Spécifier un chainage de début
            chainage_f: Spécifier un chainage de début
            interval_chainage: Spécifier un interval de chainage
            initial_offset: Spécifier un offset pour trouver les voies
        """
        # Assurer que les étapes précédante ont été faite
        if self.current_step() == 0: raise Exception("L'index BGR surfacique doit être créé avant de créer les devers.")
        # Vérifier si l'étape à déjà été faite pour l'analyse
        elif self.current_step() != 1: raise Exception("Les devers ont déjà été créés.")

        # Définir les paramètres si besoin
        if "feat_rtss" in kwargs: self.feat_rtss = kwargs["feat_rtss"]
        if "chainage_d" in kwargs: self.limit_chainage_d = kwargs["chainage_d"]
        if "chainage_f" in kwargs: self.limit_chainage_f = kwargs["chainage_f"]
        if "interval_chainage" in kwargs: self.interval_chainage = kwargs["interval_chainage"]
        if "initial_offset" in kwargs: self.initial_offset = kwargs["initial_offset"]

        # Assurer qu'un FeatRTSS a été  spécifier
        if self.feat_rtss is None: raise Exception("Veuillez définir un feat_rtss!")
        # Assurer que les limite des chainages son valide
        if self.limit_chainage_d is None or self.limit_chainage_f is None:
            raise Exception("Veuillez définir les limites de chainage (chainage_d et chainage_f)!")
        
        # Parcourir les intervalle de chainages 
        for c in range(int(self.limit_chainage_d), int(self.limit_chainage_f), self.interval_chainage):
            # Créer une géometrie d'un transect perpendiculaire au RTSS pour le chainage
            geom = self.feat_rtss.geocoderLineFromChainage([c, c], [self.initial_offset*-1, self.initial_offset])
            # Creer une list de devers pour les voie trouver
            list_of_devers:list[VoieDevers] = []
            # Créer une liste de devers optionnelle pour les cas que la fin des voie arrive au chainage spécifier
            list_of_devers_2:list[VoieDevers] = []
            # Parcourir toute les voie qui intersecte le transect
            for id in self._voie_spatial_index.intersects(geom.boundingBox()):
                # Retrouver son feature
                feat = self._voie_index[id]
                # Skip la voie si elle n'est pas sur le même rtss
                if self.feat_rtss.getRTSS() != feat[self.field_rtss_voie]: continue
                # Vérfier si les géométrie s'intersectio réellement
                if feat.geometry().intersects(geom):
                    # Gecocoder une LineRTSS à partir de la géometrie d'intersection
                    line_rtss = self.feat_rtss.geocoderInverseLine(feat.geometry().intersection(geom))
                    # Ajouter la VoieDevers si le chainage est flush avec le chainage courrant
                    if c == feat[self.field_chainage_fin_voie]: list_of_devers_2.append(VoieDevers.from_line_rtss(line_rtss))
                    # Sinon ajouter directement la VoieDevers à la liste
                    else: list_of_devers.append(VoieDevers.from_line_rtss(line_rtss))

            # TODO: Permettre 1 voies ou plus 
            # Assurer que 2 voies maximum ont été trouvé
            if len(list_of_devers) > 2: raise Exception(f"Plus de deux voies RTSS trouvées pour le chainage {c}. Veuillez vérifier les données BGR surfacique.") 
            # Vérifier si moins de 2 voies ont été trouver
            elif len(list_of_devers) < 2:
                # Vérifier si l'option 2 contient elle 2 voies 
                if len(list_of_devers_2) == 2: list_of_devers = list_of_devers_2
                # Sinon c'est qu'il manque des voies
                else: raise Exception(f"Moins de deux voies RTSS trouvées pour le chainage {c}. Veuillez vérifier les données BGR surfacique.") 
            # Ajouter les VoieDevers à l'index
            self._index_devers[c] = list_of_devers
        # Indique que l'étape à été complétéer
        self._has_devers = True

    def analyser_devers(self, mnt_path:str, mnt_crs:QgsCoordinateReferenceSystem=None):
        """
        Permet d'analyser les élévations et pentes des devers créer à partir d'un MNT.

        Args:
            mnt_path (str): Le chemin vers le MNT à utiliser
            mnt_crs (QgsCoordinateReferenceSystem, optional): Spécifier une projection au MNT. Defaults to same as voie.
        """
        # Assurer que les étapes précédante ont été faite
        if self.current_step() == 0: raise Exception("L'index BGR surfacique doit être créé avant d'analyser les devers.")
        elif self.current_step() == 1: raise Exception("Les devers doivent être créés avant de les analyser.")
        # Vérifier si l'étape à déjà été faite pour l'analyse
        elif self.current_step() != 2: raise Exception("Les devers ont déjà été analysés.")
        # Vérifier si le MNT existe bien 
        if not os.path.exists(mnt_path): raise FileNotFoundError(f"Le fichier MNT n'existe pas: {mnt_path}")
        # Définir le CRS du MNT
        if mnt_crs is None: mnt_crs = self.crs()
        else: mnt_crs = QgsCoordinateReferenceSystem(mnt_crs)

        # Parcourir les intervalles de chainages dans l'index des voies
        for c, list_voie_devers in self._index_devers.items():
            # Parcourir les devers de la liste
            for voie_devers in list_voie_devers:
                # Parcourir les points de mesures du devers
                for mesure_point in voie_devers:
                    # Définir la position du point de mesure avec le geocodage
                    mesure_point.set_position(self.feat_rtss.geocoderPointFromChainage(c, mesure_point.offset_bande()))
                    # Définir l'élévation (z) du point de mesure
                    mesure_point.set_z(self.get_mean_elevation(mnt_path, reprojectPoint(mesure_point, self.crs(), mnt_crs), 0.1))
                # Calculer les pentes du devers avec les points de mesure défini
                voie_devers.calculate_slopes()
        # Indique que l'étape à été complétéer
        self._has_analyse = True

    def output_data_frames(self, **kwargs):
        """
        Permet de créer un Dataframe Pandas qui contient les résultats a exporter en Excel
        
        kwargs:
            formater_rtss (bool): Indiquer si le RTSS devrait être formaté ou pas. Défault to False 
            formater_chainage (bool): Indiquer si les chainage devraient être formaté ou pas. Défault to False
            slopes_precision (int): Indiquer la précision des mesures de pentes. Défault to 1
        """
        # Assurer que les étapes précédante ont été faite
        if self.current_step() != 3: raise Exception("Les devers doivent être analysés avant de créer les couches de sortie.")

        # Définir la précision des pentes
        nbr_dec = kwargs.get("slopes_precision", 1)
        # Garder une suivi du dernier centre analyser pour la pente longitudinal
        last_center_point = None
        # Dictionnaire utiliser pour la création du Dataframe
        data_frame = {}
        # Parcourir les intervalle de chainage
        for c, list_voie_devers in self._index_devers.items():
            # Lister des pentes selon leurs côtées de la trace
            slopes_g, slopes_d = [], []
            largeur_corridor = 0
            # Parcourir les voies des la liste
            for voie_devers in sorted(list_voie_devers, key=lambda x: x.offset(), reverse=True):
                # Parcourir les pentes résultante du devers et ajouter les pentes au liste des pentes
                if voie_devers.side() == 1: slopes_d.extend([slope.slope() for slope in sorted(voie_devers.slopes(), key=lambda x: x.index())])
                else: slopes_g.extend([slope.slope() for slope in sorted(voie_devers.slopes(), key=lambda x: x.index())])
                largeur_corridor += voie_devers.largeur()
            # Définir le point central de la trace pour la pente longitudinale
            center_point = voie_devers.center_mesurement_point()
            # Calculer la pente longitudinal entre le point précédant et le point suivant
            if last_center_point: pente_longitudinale = ((center_point.z() - last_center_point.z()) / self.interval_chainage ) * 100
            else: pente_longitudinale = 0
            # Conserver le point pour le prochaine
            last_center_point = center_point
            # Remplir le dictionnaire avec les valeurs 
            data_frame[c] = {
                "RTSS": self.feat_rtss.getRTSS().value(formater=kwargs.get("formater_rtss", False)),
                "chainage": Chainage(c).value(formater=kwargs.get("formater_chainage", False)),
                "g_moyenne": round(np.mean(slopes_g), nbr_dec) if slopes_g else None,
                "g6": round(slopes_g[5], nbr_dec),
                "g5": round(slopes_g[4], nbr_dec),
                "g4": round(slopes_g[3], nbr_dec),
                "g3": round(slopes_g[2], nbr_dec),
                "g2": round(slopes_g[1], nbr_dec),
                "g1": round(slopes_g[0], nbr_dec),
                "d1": round(slopes_d[0], nbr_dec),
                "d2": round(slopes_d[1], nbr_dec),
                "d3": round(slopes_d[2], nbr_dec),
                "d4": round(slopes_d[3], nbr_dec),
                "d5": round(slopes_d[4], nbr_dec),
                "d6": round(slopes_d[5], nbr_dec),
                "d_moyenne": round(np.mean(slopes_d), nbr_dec) if slopes_d else None,
                "pente_long":round(pente_longitudinale, nbr_dec),
                "largeur_corridor": largeur_corridor          
            }
        # Créer et retourner le DataFrame à partir du dictionnaire des résultats
        return pd.DataFrame.from_dict(data_frame, orient='index')

    def output_layers(self, layer_point_name="Point de mesure", layer_line_name="Pente", layer_polygon_name="Devers"):
        """
        Créer les QgsVectorLayer en mémoire pour visualisé les résultats

        Args:
            layer_point_name (str, optional): Le nom de la couche des point de mesure. Defaults to "Point de mesure".
            layer_line_name (str, optional): Le nom de la couche des pentes de devers linéaire. Defaults to "Pente".
            layer_polygon_name (str, optional): Le nom de la couche des pentes de devers polygonale. Defaults to "Devers".

        Returns: Un dictionnaire avec le nom de la couche et la couche correspondante
        """
        if self.current_step() != 3: raise Exception("Les devers doivent être analysés avant de créer les couches de sortie.")

        # Création des couches qui représentent les devers
        layer_points = self.create_point_layer()
        layer_lines = self.create_line_layer()
        layer_poly = self.create_polygon_layer()

        # Créer les liste des features pour chaque couche
        feats_point, feats_lines, feat_poly = [], [], []

        # Parcourir les intervalle de chainage
        for c, list_voie_devers in self._index_devers.items():
            for voie_devers in list_voie_devers:
                # Parcourir les points de mesures du devers
                for mesure_point in voie_devers:
                    # Créer les attributs du feature
                    atts = {0:c, 1:mesure_point.name(), 2:mesure_point.offset_bande(), 3:mesure_point.z()}
                    # Créer le QgsFeature et ajouter à la liste
                    feats_point.append(QgsVectorLayerUtils.createFeature(layer_points, QgsGeometry.fromPointXY(mesure_point), atts))

                # Parcourir les pentes résultante du devers
                for slope in voie_devers.slopes():
                    # Créer les attributs du feature
                    atts = {0:c, 1:slope.name(), 2:slope.slope()}
                    # Créer une géométrie polygonale qui représente l'interpolation du devers
                    geom = self.feat_rtss.geocoderPolygonFromChainage(
                        chainages=[c+self.interval_chainage/2, c+self.interval_chainage/2, c-self.interval_chainage/2, c-self.interval_chainage/2],
                        offsets=[slope.p1().offset_bande(), slope.p2().offset_bande(), slope.p2().offset_bande(), slope.p1().offset_bande()])
                    # Créer le QgsFeature et ajouter à la liste
                    feats_lines.append(QgsVectorLayerUtils.createFeature(layer_lines, slope.as_geometry(), atts))
                    # Créer le QgsFeature et ajouter à la liste
                    feat_poly.append(QgsVectorLayerUtils.createFeature(layer_poly, geom, atts))

        # Add features to the layer
        layer_points.dataProvider().addFeatures(feats_point)
        layer_lines.dataProvider().addFeatures(feats_lines)
        layer_poly.dataProvider().addFeatures(feat_poly)
        # Retourner un dictionnaire avec le nom de la couche et la couche correspondante
        return {layer.name(): layer for layer in [layer_points, layer_lines, layer_poly]}

    @staticmethod
    def create_point_layer(layer_name="Point de mesure"):
        # Create memory layer
        layer = QgsVectorLayer(f"Point?crs=EPSG:3798", layer_name, "memory")
        
        # Get data provider
        provider = layer.dataProvider()
        
        # Add fields
        fields = [
            QgsField("chainage", QVariant.Int),
            QgsField("bande", QVariant.String), 
            QgsField("offset_bande", QVariant.Double),
            QgsField("z", QVariant.Double)]
        
        provider.addAttributes(fields)
        layer.updateFields()
        
        return layer

    @staticmethod
    def create_line_layer(layer_name="Pente"):
        # Create memory layer
        layer = QgsVectorLayer(f"LineString?crs=EPSG:3798", layer_name, "memory")
        
        # Get data provider
        provider = layer.dataProvider()
        
        # Add fields
        fields = [
            QgsField("chainage", QVariant.Int),
            QgsField("bande", QVariant.String),
            QgsField("slope", QVariant.Double)]
        
        provider.addAttributes(fields)
        layer.updateFields()
        
        return layer

    @staticmethod
    def create_polygon_layer(layer_name="Devers"):
        # Create memory layer
        layer = QgsVectorLayer(f"Polygon?crs=EPSG:3798", layer_name, "memory")
        
        # Get data provider
        provider = layer.dataProvider()
        
        # Add fields
        fields = [
            QgsField("chainage", QVariant.Int),
            QgsField("bande", QVariant.String),
            QgsField("slope", QVariant.Double)]
        
        provider.addAttributes(fields)
        layer.updateFields()
        
        return layer

    @staticmethod
    def get_mean_elevation(raster_path, point:QgsPointXY, search_distance):
        """
        Calculate mean elevation around a point within a search distance
        
        Args:
            raster_path (str): Path to the raster file
            point (QgsPointXY): The point for which to calculate the mean elevation 
            search_distance (float): Search radius in map units
            
        Returns:
            float: Mean elevation value of pixels within search distance
        """
        if search_distance <= 0: 
            return None
            
        # Open the raster dataset
        dataset = gdal.Open(raster_path)
        if dataset is None:
            raise Exception("Could not open the raster dataset.")
        
        # Get the geotransformation
        geotransform = dataset.GetGeoTransform()
        
        # Convert world coordinates to pixel coordinates
        point_col = int((point.x() - geotransform[0]) / geotransform[1])
        point_row = int((point.y() - geotransform[3]) / geotransform[5])

        # Calculate the window size in pixels
        pixel_radius = int(search_distance / abs(geotransform[1]))
        
        # Calculate window bounds
        min_col = max(0, point_col - pixel_radius)
        max_col = min(dataset.RasterXSize, point_col + pixel_radius + 1)
        min_row = max(0, point_row - pixel_radius)
        max_row = min(dataset.RasterYSize, point_row + pixel_radius + 1)
        
        # Read the data within the window
        band = dataset.GetRasterBand(1)
        data = band.ReadAsArray(min_col, min_row, 
                            max_col - min_col, 
                            max_row - min_row)
        
        if data is None or data.size == 0:
            return None
            
        # Calculate mean of valid values (exclude NoData)
        nodata = band.GetNoDataValue()
        if nodata is not None:
            valid_data = data[data != nodata]
            if valid_data.size > 0:
                return float(np.mean(valid_data))
            return None
        
        return float(np.mean(data))