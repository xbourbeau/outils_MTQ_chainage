# -*- coding: utf-8 -*-
# Importer les objects du module core de QGIS 
from qgis.core import (QgsGeometry, QgsPointXY, QgsVectorLayer, QgsField,
                        QgsCoordinateReferenceSystem, QgsSpatialIndex, QgsFeature, QgsWkbTypes, QgsFeatureIterator)
from qgis.PyQt.QtCore import QVariant
from collections import Counter
# Importer les fonction de formatage du module
from ..fnt.format import verifyFormatPoint
from ..fnt.layer import validateLayer

from ..search.SearchEngine import SearchEngine

# Importer la librairie pour des opérations trigo
import numpy as np
import copy
from typing import Union, Dict
from scipy.stats import linregress

# Librairie MTQ
from .FeatRTSS import FeatRTSS
from .Chainage import Chainage
from .LineRTSS import LineRTSS
from .RTSS import RTSS
from .PointRTSS import PointRTSS
from .PolygonRTSS import PolygonRTSS

from ..param import (DEFAULT_NOM_COUCHE_RTSS, DEFAULT_NOM_CHAMP_RTSS,
                     DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, DEFAULT_NOM_CHAMP_FIN_CHAINAGE)

class Geocodage:
    """ Une class qui permet d'éffectuer des oppérations de géocodage à partir d'une couche de RTSS. """
    
    def __init__ (self, rtss_features:QgsFeatureIterator,
                  crs:QgsCoordinateReferenceSystem,
                  nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS,
                  nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE,
                  nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                  precision=0,
                  **kwargs):
        """ 
        Initialisation de la class de géocodage avec une couche contenant les RTSS à utiliser.
        La class conserve en mémoire seulement les geometries et les informations des deux champs.
        L'instance du QgsVectorLayer peut donc être supprimé sans problème. 
        
        * Les valeurs par défault sont les noms des champs de la couche BGR - RTS du WFS 
        Args:
            - rtss_features(QgsFeatureIterator): La couche des RTSS
            - crs (QgsCoordinateReferenceSystem): Le sytème de coordonnée de la couche
            - nom_champ_rtss (str): Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int): Précison du chainage, Nombre de chiffre après la virgule
            - kwargs: Attributs suplémentaire du RTSS (nom de l'attribut = nom du champs de la valeur)
        """
        # Nom des champs de la couche RTSS
        self.nom_champ_rtss = nom_champ_rtss
        self.nom_champ_long = nom_champ_long
        self.nom_champ_chainage_d = nom_champ_chainage_d
        self.spatial_index = None
        self.setPrecision(precision)
        # Référence des RTSS
        self.dict_rtss:Dict[RTSS, FeatRTSS] = {}
        # Référence des id RTSS
        self.dict_ids:Dict[int, RTSS] = {}
        # Créer l'engine de recherche des RTSS
        self.search_engine = SearchEngine()
        # Référence du system de coordonnée
        self.setCRS(crs)
        # Créer la référence des RTSS
        self.updateRTSS(rtss_features, **kwargs)
    
    @classmethod
    def fromLayer(cls, layer:QgsVectorLayer,
                  nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS,
                  nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE,
                  nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                  precision=0,
                  **kwargs):
        """ 
        Constructeur avec la couche QgsVectorLayer des RTSS
        
        Args:
            - layer (QgsVectorLayer): La couche des RTSS
            - nom_champ_rtss (str): Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int): Précison du chainage, Nombre de chiffre après la virgule
            - interpolate_on_rtss (bool): L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
        """
        if isinstance(layer, QgsVectorLayer): 
            return cls(
                rtss_features=layer.getFeatures(), 
                crs=layer.crs(),
                nom_champ_rtss=nom_champ_rtss,
                nom_champ_long=nom_champ_long,
                nom_champ_chainage_d=nom_champ_chainage_d,
                precision=precision,
                **kwargs)
        else: return cls(None, None)

    @classmethod
    def fromProject(cls,
                    layer_name=DEFAULT_NOM_COUCHE_RTSS,
                    nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS,
                    nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE,
                    nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                    precision=0,
                    **kwargs):
        """ 
        Constructeur avec le nom de la couche des RTSS dans le projet courrant
        
        Args:
            - layer_name (str): Le nom de la couche des RTSS dans le projet
            - nom_champ_rtss (str): Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int): Précison du chainage, Nombre de chiffre après la virgule
            - kwargs: Attributs suplémentaire du RTSS (nom de l'attribut = nom du champs de la valeur)
        """
        layer = validateLayer(layer_name, [nom_champ_rtss, nom_champ_long], geom_type=1)
        
        if layer: return cls(
            rtss_features=layer.getFeatures(),
            crs=layer.crs(),
            nom_champ_rtss=nom_champ_rtss,
            nom_champ_long=nom_champ_long,
            nom_champ_chainage_d=nom_champ_chainage_d,
            precision=precision,
            **kwargs)
        else: return cls(None, None)
    
    @classmethod
    def fromSelf(cls, geocode):
        """ Constructeur de l'objet Geocodage à partir d'un autre objet Geocodage """
        new_geocode = cls(
            rtss_features=None,
            crs=geocode.getCrs(),
            nom_champ_rtss=geocode.nom_champ_rtss,
            nom_champ_long=geocode.nom_champ_long,
            nom_champ_chainage_d=geocode.nom_champ_chainage_d,
            precision=geocode.precision)
        new_geocode.dict_ids = geocode.dict_ids
        new_geocode.dict_rtss = geocode.dict_rtss
        new_geocode.spatial_index = geocode.spatial_index
        return new_geocode

    def __repr__ (self): return f"Geocodage ({len(self)} RTSS)"
    
    def __getitem__(self, key): 
        try: return self.dict_rtss[RTSS(key)]
        except: raise KeyError(f"Le RTSS ({key}) n'est pas dans le module de geocodage")

    def __len__(self): return len(self.dict_rtss)

    def __iter__ (self): return self.dict_rtss.__iter__()

    def __contains__(self, key): return RTSS(key) in self.dict_rtss

    def __deepcopy__(self, memo):
        new_obj = self.__class__.__new__(self.__class__)

        # Add the new object to the memo dictionary to avoid infinite recursion
        memo[id(self)] = new_obj

        # Deep copy all the attributes
        for k, v in self.__dict__.items():
            # Use the copy method for QgsGeometry objects
            if isinstance(v, QgsCoordinateReferenceSystem): setattr(new_obj, k, QgsCoordinateReferenceSystem(v))
            elif isinstance(v, QgsSpatialIndex): setattr(new_obj, k, QgsSpatialIndex(v))
            else: setattr(new_obj, k, copy.deepcopy(v, memo))

        return new_obj

    def createLine(self, rtss, chainages:list, offsets:list=[0]):
        """ Permet de créer un objet LineRTSS sur un RTSS """
        feat_rtss = self.get(rtss)
        return feat_rtss.createLine(chainages=chainages, offsets=offsets)

    def createPoint(self, rtss, chainage, offset=0):
        """ Permet de créer un objet PointRTSS sur un RTSS """
        feat_rtss = self.get(rtss)
        return feat_rtss.createPoint(chainage=chainage, offset=offset)
    
    def createPolygon(self, rtss, chainages:list, offsets:list):
        """ Permet de créer un objet PolygonRTSS sur un RTSS """
        feat_rtss = self.get(rtss)
        return feat_rtss.createPolygon(chainages=chainages, offsets=offsets)

    def get(self, rtss:Union[RTSS, str]) -> FeatRTSS:
        """ 
        Fonction qui retourne l'instance de la class FeatRTSS pour un RTSS.
        Retourne une valeur vide si le RTSS n'existe pas.
        
        Args:
            - rtss(str/RTSS): Le numéro de RTSS à chercher
            
        Return (FeatRTSS): L'objet FeatRTSS du RTSS
        """ 
        # Retourner la classe featRTSS si le RTSS existe dans le dictionnaire
        try: rtss = RTSS(rtss)
        except: pass
        return self.dict_rtss.get(rtss, None)

    def getAtlasLayer(self, list_locs:list[LineRTSS], width, height, overlap=20, start_offset=10, vertical_margin=10, chainage_exact=False):
        """
        Méthode qui permet de générer des polygones le long d'un RTSS. 
        Ces polygon sont concu pour être utiliser comme atlas pour une carte. Ils sont placer de manière 
        à s'assurer que toutes le RTSS contenue dans le polygon est entièrement contenu à l'interieur du polygon. 

        Source:
        Polystrip plugin:
            begin                : 2017-07-29
            git sha              : $Format:%H$
            copyright            : (C) 2017 by Werner Macho
            email                : werner.macho@gmail.com 
        following code mostly taken from
        https://gis.stackexchange.com/questions/173127/generating-equal-sized-polygons-along-line-with-pyqgis

        Args:
            - list_start_points (list): Liste des objets PointRTSS des débuts d'atlas
            - width (float): Largeur des polygones en mètres
            - height (float): Hauteur des polygones en mètres
            - list_end_points (list): Liste des objets PointRTSS des fins d'atlas
            - overlap (int): Pourcentage de recouvrement entre les polygons
            - start_offset (int): Pourcentage de la longeurs du premier polygone qui est décaler pour convrir le début
            - vertical_margin (int): Pourcentage de la hauteur des marges verticales que le RTSS ne doit pas dépasser
            - chainage_exact (bool): Déterminer les chainages excate des débuts/fin des polygons

            Return (QgsVectorLayer): La couche contenant toutes les entitées des pages d'atlas
        """
        # Create the atlas pages layer
        layer_pages = QgsVectorLayer(f"Polygon?crs={str(self.getEpsg())}", "Atlas_pages", "memory")
        field_chainage_type = QVariant.Int if self.precision == 0 else QVariant.Double
        # Ajouter les champs de la couche
        attributes = [
            QgsField("rtss", QVariant.String),
            QgsField("chainage_d", field_chainage_type),
            QgsField("chainage_f", field_chainage_type),
            QgsField("angle", QVariant.Double)]
        layer_pages.dataProvider().addAttributes(attributes)
        layer_pages.updateFields()
        
        page_features = []
        for line in list_locs:
            # Parcourir les informations des pages de l'atlas
            for page in self.getAtlasPages(line, width, height, overlap=overlap, start_offset=start_offset, vertical_margin=vertical_margin, chainage_exact=chainage_exact):
                # Create new page feature
                feat = QgsFeature()
                atts = list(page["atts"].values())
                atts[0] = str(atts[0])
                if field_chainage_type == QVariant.Int:
                    atts[1] = int(atts[1])
                    atts[2] = int(atts[2])
                else:
                    atts[1] = float(atts[1])
                    atts[2] = float(atts[2])
                feat.setAttributes(atts)
                feat.setGeometry(page["geom"])
                page_features.append(feat)
        if page_features: layer_pages.dataProvider().addFeatures(page_features)
        # Retourner la couche 
        return layer_pages
    
    def getAtlasPages(self, line:LineRTSS, width, height, overlap=20, start_offset=10, vertical_margin=10, chainage_exact=False):
        """
        Méthode qui permet de générer des polygones le long d'un RTSS. 
        Ces polygon sont concu pour être utiliser comme atlas pour une carte. Ils sont placer de manière 
        à s'assurer que toutes le RTSS contenue dans le polygon est entièrement contenu à l'interieur du polygon. 

        Args:
            - line (LineRTSS): La ligne sur laquelle générer des atlas
            - width (float): Largeur des polygones en mètres
            - height (float): Hauteur des polygones en mètres
            - end (PointRTSS): PointRTSS de la fin de l'atlas
            - overlap (int): Pourcentage de recouvrement entre les polygons
            - start_offset (int): Pourcentage de la longeurs du premier polygone qui est décaler pour convrir le début
            - vertical_margin (int): Pourcentage de la hauteur des marges verticales que le RTSS ne doit pas dépasser
            - chainage_exact (bool): Déterminer les chainages excate des débuts/fin des polygons

            Return: 
                - dict: [{"atts": {"rtss": RTSS, "chainage_d": chainage de début, "chainage_f": chainage de fin, "angle": l'angle de la page}, "geom": La geometry de la page}, ...]
        """
        # BUG: La vérification que le rtss est entièrement couvert est valide seulement de manière vertical.
        atlas_pages_info = []
        feat_rtss = self.get(line.listRTSS()[0])
        # Définir les informations de la ligne
        geometrie = feat_rtss.geocoderLine(line)
        extended_geom = QgsGeometry.extendLine(geometrie, (start_offset/100) * width, (start_offset/100) * width)
        geom_length = extended_geom.length() 
        # Position du curseur en pourcentage (0 à 1)
        curs, forward = 0, 0
        # Définir le pas entre chaque page (0 à 1)
        step = 1.0 / (geom_length / width)
        # Définir la distance maximun entre le center vertical du polygon et ça hauteur
        tolerance_margin = (1.0 - (vertical_margin/100)) * (height/2)
        # Définir le pas de reculons entre chaque page pour avoir le overlap (0 à 1)
        stepnudge = (1.0 - (overlap/100))
        while curs <= 1 and forward < 1:
            # Get the first point for the polygon
            start_point = extended_geom.interpolate(curs * geom_length)
            # Definir la modification du pas à appliquer si la page de couvre pas la ligne
            best_step = 1
            # Distance maximum du RTSS et du centre vertical de la page
            vertical_dist_max = tolerance_margin
            # Continuer tant que la distance maximum est plus grande que la tolérance
            while vertical_dist_max >= tolerance_margin and best_step > 0.1:
                # Définir la position du point de fin 
                forward = curs + (best_step * step)
                # Position maximal est de 1
                if forward > 1: forward = 1
                # Définir le point de fin
                end_point = extended_geom.interpolate(forward * geom_length)
                # Définir la liste des points de la partie du RTSS utiliser pour générer la page
                line_geom = [start_point.asPoint()]
                for i, vertice in enumerate(extended_geom.vertices()):
                    # Vertex sous forme de geometry
                    vertice_geom = QgsGeometry().fromPointXY(QgsPointXY(vertice))
                    current_dist = extended_geom.lineLocatePoint(vertice_geom)
                    if current_dist >= extended_geom.lineLocatePoint(end_point): break
                    elif current_dist > extended_geom.lineLocatePoint(start_point): line_geom.append(vertice_geom.asPoint())
                line_geom.append(end_point.asPoint())
                # Extract x and y coordinates from points
                x_coords, y_coords = [point.x() for point in line_geom], [point.y() for point in line_geom]
                # Perform linear regression
                slope, intercept, _, _, _ = linregress([x_coords[0], x_coords[-1]], [y_coords[0], y_coords[-1]])
                # Calculate distances maximum from each point to the regression line
                vertical_dist_max = max([abs(y - (slope * x + intercept)) / np.sqrt(slope**2 + 1) for x, y in zip(x_coords, y_coords)])
                best_step -= 0.1
                
            # Construire la geometrie de la page
            page_geom = QgsGeometry().fromWkt('POLYGON((0 0, 0 {height},{width} {height}, {width} 0, 0 0))'.format(height=height, width=width))
            page_geom.translate(0, -height/2)
            currangle = (start_point.asPoint().azimuth(end_point.asPoint())+270) % 360
            page_geom.rotate(currangle, QgsPointXY(0, 0))
            page_geom.translate(start_point.asPoint().x(), start_point.asPoint().y())
            page_geom.asPolygon()
            
            chainage_d = self.roundChainage(feat_rtss.getChainageFromPoint(start_point))
            chainage_f = self.roundChainage(feat_rtss.getChainageFromPoint(end_point))
            if chainage_exact:
                # Intersections entre le périmètre de la page et le RTSS
                intersection = feat_rtss.geometry().intersection(QgsGeometry.fromPolylineXY(page_geom.asPolygon()[0]))
                if intersection:
                    # Calculer les valeurs de chainages des points d'intersections
                    if intersection.wkbType() == QgsWkbTypes.MultiPoint: intersect_list = sorted([self.roundChainage(feat_rtss.getChainageFromPoint(point)) for point in intersection.asMultiPoint()])
                    else: intersect_list = [self.roundChainage(feat_rtss.getChainageFromPoint(intersection.asPoint()))]
                    # Liste des chainages plus grand que celui de début
                    chainages_potentiel_f = [chainage for chainage in intersect_list if chainage > chainage_d]
                    if len(chainages_potentiel_f) != 0: chainage_f = chainages_potentiel_f[0]
            # Create new page info
            page_info = {"atts": {"rtss": feat_rtss.getRTSS(), "chainage_d": chainage_d, "chainage_f": chainage_f, "angle": currangle}, "geom": page_geom}
            atlas_pages_info.append(page_info)
            # Advance current position
            curs += stepnudge * best_step * step
            
        return atlas_pages_info

    def getEpsg(self):
        """ Retourne le EPSG courrant de l'object """ 
        if isinstance(self.crs, QgsCoordinateReferenceSystem): return self.crs.authid()
        else: return None
    
    def getCrs(self):
        """ Retourne le CRS courrant de l'object """
        return self.crs
    
    def getRTSSById(self, id):
        # Vérifier si le RTSS existe dans le dictionnaire 
        try: return self.dict_rtss[self.dict_ids[id]]
        except: raise KeyError("L'identifant du QgsFeature du RTSS n'est pas dans le module de geocodage")
    
    def getRTSSFromText(self, rtss:Union[RTSS, str])->list[FeatRTSS]:
        """ 
        Fonction qui retourne un liste des objet FeatRTSS qui commence par un text
        
        Args:
            - rtss(str/RTSS): Le numéro de RTSS à chercher
            
        Return (list): Liste des objet FeatRTSS qui commence par la valeur demander
        """ 
        # Retourner les FeatRTSS qui commence
        if not isinstance(rtss, str): rtss = str(rtss)
        rtss = rtss.upper()
        rtss = ''.join([i for i in rtss if i in "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"])
        return [val for val in self.dict_rtss.values() if val.startWith(rtss)]

    def getListRTSS(self, formater=True, sorted=False):
        """
        Méthode qui permet de retourner la liste de toutes les numéros de RTSS du module de géocodage
        Les RTSS sont retourner sous forme de text.
        Args:
            - formater (bool): Formater les numéros de RTSS
            - sorted (bool): Ordonner en ordre croissant la liste des RTSS
        """
        # Liste de toutes les RTSS et formater la liste si nécéssaire
        list_rtss = [rtss.value(formater=formater) for rtss in self.dict_rtss.keys()]
        # Trier la liste si nécéssaire
        if sorted: list_rtss.sort()
        # Retourner la liste
        return list_rtss
        
    def getListFeatRTSS(self):
        """ Méthode qui permet de retourner la liste de toutes les objets FeatRTSS du module de géocodage """
        # Retourner la liste de toutes les featRTSS
        return list(self.dict_rtss.values())
    
    def geocoder(self, object_rtss:Union[PointRTSS,LineRTSS,PolygonRTSS], on_rtss=False):
        feat_rtss = self.get(object_rtss.getRTSS())
        # Retourner la géometries géocoder sur le RTSS
        if isinstance(object_rtss, PointRTSS):
            return feat_rtss.geocoderPoint(object_rtss, on_rtss=on_rtss)
        if isinstance(object_rtss, LineRTSS):
            return feat_rtss.geocoderLine(object_rtss, on_rtss=on_rtss)
        if isinstance(object_rtss, PolygonRTSS):
            return feat_rtss.geocoderPolygon(object_rtss)

    def geocoderFromChainages(self, rtss:Union[RTSS, str], chainages:list, offsets:list=[0], interpolate_on_rtss=True):
        """
        Permet de géocoder une géometry selon une liste de chainage.
            Point: Contient un chainage
            Line: Contient plus d'un chainage
            Polygon: Le premier point est le même que le dernier

        Args:
            - rtss (RTSS/str): La valeur du RTSS de la géometrie
            - chainages (list): Liste des chainages 
            - offsets (list): Liste des offset
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points

        return (QgsGeometry): La géometrie géocoder
        """
        feat_rtss = self.get(rtss)
        if len(chainages) == 1: 
            return feat_rtss.geocoderPointFromChainage(chainages[0], offset=offsets[0])
        elif len(chainages) > 1:
            return feat_rtss.geocoderLineFromChainage(
                chainages=chainages,
                offsets=offsets,
                interpolate_on_rtss=interpolate_on_rtss)
        else: return QgsGeometry()

    def geocoderPoint(self, point:PointRTSS, on_rtss=False):
        """
        Permet de géocoder un PointRTSS en QgsGeometry sur sont RTSS.

        Args:
            - point(PointRTSS): Le point à géocoder
            - on_rtss(bool): Permet d'overide la valeur de offset en géocodant le point sur le RTSS 
        
        Return (QgsGeometry): La géometrie du point géocoder
        """
        feat_rtss = self.get(point.getRTSS())
        # Retourner la géometries géocoder sur le RTSS
        return feat_rtss.geocoderPoint(point, on_rtss=on_rtss)
    
    def geocoderPolygon(self, polygon:PolygonRTSS):
        """
        Permet de géocoder une LineRTSS en QgsGeometry sur sont RTSS.

        Args:
            - polygon(PolygonRTSS): Le polygon à géocoder
        
        Return (QgsGeometry): La géometrie du polygon géocoder
        """
        # TODO: Faire en sorte qu'on puisse géocoder un polygon sur plus d'un RTSS
        for rtss in polygon.listRTSS():
            feat_rtss = self.get(rtss)
            # Retourner la géometries géocoder sur le RTSS
            return feat_rtss.geocoderPolygon(polygon)

    def geocoderLine(self, line:LineRTSS, on_rtss=False):
        """
        Permet de géocoder une LineRTSS en QgsGeometry sur sont RTSS.

        Args:
            - line(LineRTSS): La ligne à géocoder
            - on_rtss(bool): Permet d'overide la valeur de offset en géocodant le point sur le RTSS 
        
        Return (QgsGeometry): La géometrie de la ligne géocoder
        """
        # TODO: Faire en sorte qu'on puisse géocoder une ligne sur plus d'un RTSS
        for rtss in line.listRTSS():
            feat_rtss = self.get(rtss)
            # Retourner la géometries géocoder sur le RTSS
            return feat_rtss.geocoderLine(line, on_rtss=on_rtss)
    
    def geocoderInverse(self, geometry:QgsGeometry, rtss=None):
        """
        Méthode qui associe un RTSS/chainage à une géometrie ponctuelle ou linéaire. Un RTSS peux être spécifié
        s'il est connue. Sinon le RTSS le plus proche est selectionnée. Pour selectionnée le RTSS le plus proche,
        d'un entités linéaire, c'est la sum des distance avec le point de début et de fin.
        
        Args:
            - geometry (QgsGeometry): La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            - rtss(str): Le numéro du RTSS. Peut être formater ex: (0001002155000D ou 00010-02-155-000D)
        
        Return (PointRTSS/LineRTSS): L'objet RTSS représentant la géometrie
        """
        # Type de geometry (1 = Point et 2 = Ligne)
        geometry.convertToSingleType()
        geometry_type = geometry.wkbType()

        if geometry_type == 1: return self.geocoderInversePoint(geometry, rtss=rtss)
        elif geometry_type == 2: return self.geocoderInverseLine(geometry, rtss=rtss)
        elif geometry_type == 3: return self.geocoderInversePolygon(geometry, rtss=rtss)
    
    def geocoderInversePoint(self, geom_point:Union[QgsGeometry, QgsPointXY], rtss=None):
        """
        Méthode qui permet d'associer un RTSS/chainage à une géometrie ponctuelle. 
        Un RTSS peux être spécifié s'il est connue. Sinon le RTSS le plus proche est selectionnée.

        Args:
            - geom_point (QgsGeometry/QgsPointXY): La géometry du point à analyser
            - rtss (str): Numéro de RTSS du point à analyser
        
        Return (PointRTSS): L'objet PointRTSS représentant la géometry
        """
        geom_point = verifyFormatPoint(geom_point)
        # Aller chercher directement le featRTSS si un RTSS est défini et est dans la dictionnaire de référence
        if rtss: feat_rtss = self.get(rtss)
        # Sinon appeller la fonction pour avoir le RTSS le plus proche de la géometrie
        else: feat_rtss = self.nearestRTSSFromPoint(geom_point)
        return feat_rtss.geocoderInversePoint(geom_point)
    
    def geocoderInverseLine(self, geom_line:QgsGeometry, rtss=None, methode=1):
        """
        Convertir une geometry en objet LineRTSS

        Args:
            - geom_line (QgsGeometry) = La géometrie linéaire
            - rtss (RTSS) = Indiquer un RTSS spécifique
            - methode (int) (1 = by Extremities) (2 = by Vertex)
        
        Return: LineRTSS = L'objet LineRTSS qui représente le mieux la géometrie
        """
        if methode == 2: return self.geocoderInverseLineByVertex(geom_line, rtss)
        else: return self.geocoderInverseLineByExtremities(geom_line, rtss)

    def geocoderInverseLineByExtremities(self, geom_line:QgsGeometry, rtss=None):
        """
        Méthode qui permet de trouver le RTSS, chainage et offset des extremitées d'une ligne.

        Args:
            - geom_line (QgsGeometry): La géometry du point à analyser
            - rtss (str): Numéro de RTSS du point à analyser
        
        Return: LineRTSS = L'objet LineRTSS qui représente le mieux la géometrie
        """
        # Dictionnaire des resultats des extremitées
        list_points = []
        # Parcourir les deux extremitées de la géometrie linéaire
        for extrem in (0, -1):
            # Géocodage inverse de l'extremitées
            list_points.append(self.geocoderInversePoint(
                QgsGeometry.fromPointXY(geom_line.asPolyline()[extrem]), rtss=rtss))
        # Retourner la ligne RTSS qui représente la geometrie
        return LineRTSS(list_points)
    
    def geocoderInverseLineByVertex(self, geom_line:QgsGeometry, rtss=None):
        """
        Méthode qui permet de trouver le RTSS, chainage et offset pour chaque vertex d'une ligne.

        Args:
            - geom_line (QgsGeometry): La géometry du point à analyser
            - rtss (str): Numéro de RTSS du point à analyser
        
        Return: LineRTSS = L'objet LineRTSS qui représente le mieux la géometrie
        """
        list_points = []
        for vertex in geom_line.vertices():
            # Ajouter la valeur RTSS, chainage et offset du vertex
            list_points.append(self.geocoderInversePoint(
                QgsGeometry.fromPointXY(QgsPointXY(vertex)), rtss=rtss))
        # Retourner la ligne RTSS qui représente la geometrie
        return LineRTSS(list_points)

    def geocoderInversePolygon(self, geom_poly:QgsGeometry, rtss=None):
        """
        Convertir une geometry en objet PolygonRTSS

        Args:
            - geom_line (QgsGeometry) = La géometrie du polygon
            - rtss (RTSS) = Indiquer un RTSS spécifique
        
        Return: PolygonRTSS = L'objet PolygonRTSS qui représente le mieux la géometrie
        """
        if not geom_poly: raise NameError("La geometry du polygon a convertir est NULL")
        # Aller chercher directement le featRTSS si un RTSS est défini et est dans la dictionnaire de référence
        if rtss: feat_rtss = self.get(rtss)
        # Sinon appeller la fonction pour avoir le RTSS le plus proche de la géometrie
        else: 
            rtss = Counter([self.nearestRTSSFromPoint(QgsGeometry.fromPointXY(QgsPointXY(point))).value()
                    for point in geom_poly.vertices()])
            feat_rtss = self.get(rtss.most_common(1)[0][0])
        
        return feat_rtss.geocoderInversePolygon(geom_poly)

    def isEmpty(self): 
        """ 
        Méthode qui retourne l'indicateur le l'instantiation de la class. 
        Retourn True tant que la class n'a pas des RTTS valide
        """
        return self.dict_rtss == {}

    def nearestRTSS(self, geometry:QgsGeometry, dist_max=0)->FeatRTSS:
        """
        Retourner le FeatRTSS le plus proche d'une géometry

        Args:
            - geometry (QgsGeometry): La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            - dist_max (int): Distance maximum à tolérer pour la recherche (0=Aucune)
        """
        list_rtss = self.nearestsRTSS(geometry=geometry, nbr=1, dist_max=dist_max)
        if list_rtss == []: return None
        else: return list_rtss[0]

    def nearestRTSSFromPoint(self, geometry:QgsGeometry, dist_max=0)->FeatRTSS:
        # Parcourir la liste des id de RTSS les plus proche de la geometrie en entrée
        for id in self.spatial_index.nearestNeighbor(geometry, neighbors=1, maxDistance=dist_max):
            return self.getRTSSById(id)
        
    def nearestsRTSS(self, geometry:QgsGeometry, nbr:int=1, dist_max=0)->list[FeatRTSS]:
        """
        Méthode pour determiner les featRTSS, dans la référence des RTSS, les plus proche d'une geometrie.
        La géometrie peut être ponctuelle ou linéaire. Pour identifier le RTSS le plus proche d'une ligne,
        la moyenne des distance avec le point de début et de fin est utiliser. Cela permet de ne pas retourner 
        un RTSS qui croise une ligne à une place alors que la ligne est clairement parallel à un autre RTSS.
        
        Args:
            - geometry (QgsGeometry): La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            - nbr (int): Nombre de RTSS à proximité à retourner
            - dist_max (int): Distance maximum à tolérer pour la recherche (0=Aucune)
            
        Return:
            - liste: [FeatRTSS]
        """
        # Définir le nombre de voisin à trouver
        nbr_neighbors = nbr if nbr != 0 else 1
        list_nearest_rtss = []
        # Type de geometry (1 = Point et 2 = Ligne)
        geometry_type = geometry.wkbType()
        # Parcourir la liste des id de RTSS les plus proche de la geometrie en entrée
        for id in self.spatial_index.nearestNeighbor(geometry, neighbors=nbr_neighbors, maxDistance=dist_max):
            feat_rtss = self.getRTSSById(id)
            # La géometrie du RTSS
            rtss_geom = feat_rtss.geometry()
            # Distance entre le point et le rtss
            if geometry_type == 1: dist = rtss_geom.distance(geometry)
            # TODO: Voire si on a besoin de verifier seulement la distance des extremitées ou si on peux faire la distance sur la geometrie
            elif geometry_type == 2:
                # Liste des points de la ligne
                line = geometry.asPolyline()
                # Moyenne des distance du premier et du dernier point de la ligne avec le RTSS
                dist = sum([rtss_geom.distance(QgsGeometry().fromPointXY(pt)) for pt in [line[0], line[-1]]])/2
            # Ajouter le FeatRTSS si la distance avec la géometry est 0 ou plus petite que la distance max
            if dist <= dist_max or dist_max == 0 : list_nearest_rtss.append({'rtss':feat_rtss, 'distance':dist})
        # Ordonner la list par distance
        list_nearest_rtss.sort(key=lambda rtss : rtss['distance'])
        # Conserver seulement la liste des FeatRTSS
        list_nearest_rtss = [i["rtss"] for i in list_nearest_rtss]
        # Retourner la class featRTSS du RTSS le plus proche
        if nbr == 0: return list_nearest_rtss
        else: return list_nearest_rtss[:nbr_neighbors]
    
    def geocoderPointOnRTSS(self, point:Union[QgsPointXY, QgsGeometry], dist_max=None):
        """
        Méthode qui permet de retourner le PointRTSS le plus proche du 

        Args:
            point (Union[QgsPointXY, QgsGeometry]): Le point à géocoder sur le RTSS
            dist_max (_type_, optional): La distance maximal au RTSS. Defaults to None.

        Returns:
            PointRTSS: Le point sur le RTSS avec une geometry
        """
        point_rtss = self.geocoderInversePoint(point)
        if dist_max is None: dist_max = abs(point_rtss.getOffset())
        if abs(point_rtss.getOffset()) <= dist_max:
            point_rtss.setOffset(0)
            point_rtss.setGeometry(self.geocoderPoint(point_rtss))
            return point_rtss
        else: return None

    def getAngle(self, point_rtss:PointRTSS):
        """
        Méthode qui permet de retourner l'angle le long de la ligne à une position donnée.

        Args:
            - point_rtss (PointRTSS): Le point RTSS à évaluer
        """
        return self.getAngleAtChainage(point_rtss.getRTSS(), point_rtss.getChainage())

    def getAngleAtChainage(self, rtss:Union[RTSS, str], chainage:Union[str,int,float,Chainage]):
        """
        Méthode qui permet de retourner l'angle le long de la ligne à un chainage.

        Args:
            - rtss (str): Le numéro du RTSS
            - chainage (str/real): Le chainage pour lequel mesurer l'angle
        """
        # Instance de la class FeatRTSS contenant toute les informations du RTSS
        feat_rtss = self.get(rtss)
        # Retourner l'angle au chainage pour le RTSS
        return feat_rtss.getAngleAtChainage(chainage)
    
    def roundChainage(self, chainage:Union[str,int,float,Chainage])->Chainage:
        """ Méthode qui permet d'arrondir le chainage selon le paramètre de précision du module """
        if self.precision is None: return Chainage(chainage)
        else: return round(Chainage(chainage), self.precision)

    def search(self, search_text:str, limit=5, as_rtss=False):
        """
        Permet d'utiliser l'engine de recherche pour trouver un RTSS

        Args:
            search_text (str): Le text pour chercher les RTSS
            limit (int): Le nombre de choix de retour possible
            as_rtss (bool): Si la liste des RTSS doit être retourner sous forme d'objet RTSS
        """
        # Liste des numéros de RTSS les plus probable selon l'engin de recherche 
        list_possible_rtss = self.search_engine.search(search_text, limit=limit)
        # Convertir les numéros de RTSS en objet RTSS si spécifié
        if as_rtss: list_possible_rtss = [RTSS(rtss) for rtss in list_possible_rtss]
        # Retourner la liste des RTSS les plus probables
        return list_possible_rtss

    def setCRS(self, crs):
        """
        Méthode qui permet de définir le système de coordonnée des geometries utilisé. 
        Il doit être un instance de la class QgsCoordinateReferenceSystem de QGIS et avoir une projection en mètre
        
        Args:
            - crs (QgsCoordinateReferenceSystem): Le système de coordonnée des géometries des RTSS
        """
        self.crs = None
        if isinstance(crs, QgsCoordinateReferenceSystem):
            self.crs = crs
            self.epsg = self.crs.authid()
            # La couche des RTSS doit être projeté dans une projection en mètre
            if self.crs.mapUnits() != 0: raise Exception("L'unité de la couche des RTSS doit être en mètre.")
    
    def setPrecision(self, precision):
        """
        Méthode pour définir la précision des chainages à retourner.
        Si la précision est None, les chainages ne seront pas arrondi

        Args:
            - precision (int): La valeur pour l'arrondi (entier positif = nbr décimal / entier négatif = la dizaine)
        """
        if isinstance(precision, int): self.precision = precision
        else: self.precision = None
    
    def updateSearchEngine(self, dict_index:dict[str:list[str]]):
        """
        Permet de mettre à jour l'engin de recherche de RTSS.

        Args:
            dict_index (Dict[str, list[str]]): Le dictionnaire des index de recheche. Ex: Valeur du résultat: [list de recherche]
        """
        self.search_engine.updateSearchingIndex(dict_index)

    def updateRTSS(self, 
            rtss_features:QgsFeatureIterator,
            crs:QgsCoordinateReferenceSystem=None,
            nom_champ_rtss=None,
            nom_champ_long=None,
            nom_champ_chainage_d=None,
            **kwarg):
        """ Méthode qui permet de créer ou de mettre à jour la référence des RTSS
        
        Args:
            - rtss_features(QgsFeatureIterator): La nouvelle couche des RTSS
            - crs (QgsCoordinateReferenceSystem): Le système de coordonnée de la couche
            - nom_champ_rtss (str): Le nom du champ contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ contenant le chainage de début du RTSS
        """
        # Modifier la référence du nom du champs si un nouveau nom est défini
        if nom_champ_rtss: self.nom_champ_rtss = nom_champ_rtss
        if nom_champ_long: self.nom_champ_long = nom_champ_long
        self.nom_champ_chainage_d = nom_champ_chainage_d
        # Dictionnaire utiliser pour la recherche par RTSS
        dict_index = {}
        # Définir le nouveau CRS si défini
        if crs: self.setCRS(crs)
        # Vérifier que le CRS de la class est valide
        if self.getCrs() and rtss_features:
            # Index spatial des géometries des RTSS
            self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
            # Parcourir toutes les entités de la couche des RTSS
            for rtss in rtss_features:
                # Numéro du RTSS
                num_rts = RTSS(rtss[self.nom_champ_rtss])
                # Créer un instance de la class featRTSS
                self.dict_rtss[num_rts] = FeatRTSS.fromFeature(
                    feat=rtss,
                    nom_champ_rtss=self.nom_champ_rtss,
                    nom_champ_long=self.nom_champ_long,
                    chainage_d=self.nom_champ_chainage_d,
                    **kwarg)
                # Ajouter le RTSS à l'index des identifiants
                self.dict_ids[rtss.id()] = num_rts
                # Ajouter le RTSS à l'index spatial
                self.spatial_index.addFeature(rtss)
                # Ajouter le RTSS au dictionnaire de recherche
                dict_index[num_rts.value()] = [
                    num_rts.value(zero=False), 
                    num_rts.valueFormater(), 
                    num_rts.value(formater=True, zero=False)]
            # Mettre à jour l'engin de recherche
            self.updateSearchEngine(dict_index)