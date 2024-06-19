# -*- coding: utf-8 -*-
import copy
from typing import Union, Dict

# Importer les objects du module core de QGIS 
from qgis.core import (QgsCoordinateReferenceSystem, QgsSpatialIndex, QgsFeatureIterator,
                       QgsVectorLayer, QgsFeatureRequest)

from .Chainage import Chainage
from .RTSS import RTSS
from .LineSegmentationElement import LineSegmentationElement
from .LinearReferencing import LinearReferencing
from .Geocodage import Geocodage
from .PointRTSS import PointRTSS


class ReseauSegmenter(Geocodage):
    """ Méthode qui permet de gérer un groupe de RTSS segmentés. """

    def __init__(self, 
                geocode:Geocodage,
                reseau:Dict[RTSS, LinearReferencing]=None):
        """ 
        Initialisation de la class de géocodage avec une couche contenant les RTSS à utiliser.
        La class conserve en mémoire seulement les geometries et les informations des deux champs.
        L'instance du QgsVectorLayer peut donc être supprimé sans problème. 
        
        * Les valeurs par défault sont les noms des champs de la couche BGR - RTS du WFS 
        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau 
            - reseau (dict): Dictionnaire des objet de LinearReferencing
        """
        Geocodage.__init__(
            self,
            rtss_features=None,
            crs=geocode.getCrs(),
            nom_champ_rtss=geocode.nom_champ_rtss,
            nom_champ_long=geocode.nom_champ_long,
            nom_champ_chainage_d=geocode.nom_champ_chainage_d,
            precision=geocode.precision)
        
        self.dict_ids = geocode.dict_ids
        self.dict_rtss = geocode.dict_rtss
        self.spatial_index = geocode.spatial_index

        # Définir le réseau de segmentation
        if reseau is None: self.setReseau({})
        else: self.setReseau(reseau)

    @classmethod
    def fromLayerFields(cls, geocode, layer, champ_rtss, champ_cd, champ_cf, filter_request=QgsFeatureRequest()):
        """
        Constructeur qui permet de créer l'objet ReseauSegmenter avec toute les RTSS.
        d'un module de geocodage. Le réseau est segmenter selon le RTSS et chainage début et fin
        d'une couche en entrée. La valeur d'élément est l'identifiant de l'entité de la couche.

        Args:
            - geocode: Module de géocodage
            - layer: Le QgsVectorLayer de la couche
            - champ_rtss: Le nom du champ du RTSS des entitées
            - champ_cd: Le nom du champ du chainage de début des entitées
            - champ_cf: Le nom du champ du chainage de fin des entitées
            - filter_request (QgsFeatureRequest): Requête pour filtrer la couche en entrée
        """
        reseau_segmenter = cls.fromGeocodage(geocode)
        # Parourir toutes les entitées de la couche
        for feat in layer.getFeatures(filter_request):
            # Definir l'objet LinearReferencing
            rtss_seg = reseau_segmenter.getRTSSSegmenter(feat[champ_rtss])
            # Vérifier si l'objet LinearReferencing est valide
            if rtss_seg is None: continue
            # Définir le chainage de début de l'entitée
            cd = rtss_seg.getChainageOnRTSS(feat[champ_cd])
            # Définir le chainage de fin de l'entitée
            cf = rtss_seg.getChainageOnRTSS(feat[champ_cf])
            elem = LineSegmentationElement(feat.id(), 0)
            # Ajouter l'id du projet au module de référence linéraire du RTSS
            rtss_seg.addElement(elem, cd, cf, False)
        return reseau_segmenter

    @classmethod
    def fromLayerInterpolation(
        cls, 
        geocode:Geocodage,
        layer:QgsVectorLayer,
        field_value,
        fields_route=[],
        step=10, 
        max_dist=20):
        """
        Constructeur qui permet de créer l'objet ReseauSegmenter avec toute les RTSS.
        L'interpolation est fait en fonction du plus proche voisin. Une distance max peux être spécifier pour 
        limiter l'interpolation. De plus, le paramètre step permet de définir le pas de chainage pour calculer le voisin
        le plus proche.

        Args:
            - geocode: Module de géocodage
            - layer: Le QgsVectorLayer de la couche à interpoler
            - field_value: Le nom du champ de valeur de la couche
            - fields_route: Une liste de nom de champ dont le 5 première lettre sont le numéro de route à filtrer
            - step: La distance entre chaque point utilisé pour l'interpolation
            - max_dist: La distance maximal pour qu'un objet soit considéré sur la route 
        """
        reseau_segmenter = cls.fromGeocodage(geocode)
        # Localisation des vitesses
        spatial_index = QgsSpatialIndex(layer.getFeatures(), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        # Pourcourir toutes les modules de référence linéraire des RTSS
        for rtss_seg in reseau_segmenter.getValues():
            # Parcourir les chainages des RTSS
            for c in range(rtss_seg.chainageDebut(), rtss_seg.chainageFin(), step):
                # Géometrie du point de chainage
                point_geom = rtss_seg.geocoderPointFromChainage(c)
                # Valeurs d'ID et de distance par défault
                feat_id, min_dist = None, max_dist+1
                # Parcourir les ID des entitées à proximité
                for id in spatial_index.nearestNeighbor(point_geom.asPoint(), 5, maxDistance=max_dist):
                    # Vérifier que les numéros de routes sont les mêmes si un champs est spécifié
                    if fields_route == []: pass
                    elif not any([layer.getFeature(id)[f][:5] == rtss_seg.getRoute() for f in fields_route]): continue
                    # Calculer la vrai distances entre les deux geometry
                    distance = layer.getFeature(id).geometry().distance(point_geom)
                    # Conserver la distances la plus petite 
                    if distance < min_dist: feat_id, min_dist = id, distance
                
                # Définir la valeur 
                if feat_id is None: value = None
                else: value = layer.getFeature(feat_id)[field_value]
                # Vérifier si la valeur de la segmentation au chainage courant est la même que la valeur la plus proche
                try: 
                    if value in rtss_seg.getSegmentation(c, exact=False).getElements(): continue
                except: pass
                # Sinon ajouter une segmentation avec la valeur la plus proche au chainage courant
                rtss_seg.addElement(value, c, rtss_seg.chainageFin(), copy_elements=False)
        return reseau_segmenter

    def __repr__ (self): return f"ReseauSegmenter ({len(self.reseau)} RTSS)"

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

    def setModuleGeocodage(self, geocode:Geocodage):
        """
        Méthode qui permet de définir le module de geocodage sur lequel baser le réseau.

        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau
        """
        self.geocode = geocode
        self.reseau:Dict[RTSS, LinearReferencing] = {feat_rtss.getRTSS(): LinearReferencing.fromFeatRTSS(feat_rtss) for feat_rtss in self.geocode.getListFeatRTSS()}
    
    def addElement(self, rtss:RTSS, element:LineSegmentationElement, chainage_d:Chainage, chainage_f:Chainage, copy_elements=True):
        """
        Permet d'ajouter un élément au réseau

        Args:
            rtss (RTSS): Le rtss de l'élément
            element (LineSegmentationElement): L'élément à ajouter au réseau 
            chainage_d (Chainage): Chainage de début de l'élément
            chainage_f (Chainage): Chainage de fin de l'élément
            copy_elements (bool, optional): Conserver les éléments de la segmentation intersectée
        """
        # Aller chercher le RTSS segmenter 
        segment_rtss = self.getLinearReference(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return None
        # Ajouter l'élément au réseau
        segment_rtss.addElement(element, chainage_d, chainage_f, copy_elements=copy_elements)

    def addElementsFromLayer(self,
            feature_iter:QgsFeatureIterator,
            field_rtss,
            field_chainage_d,
            field_chainage_f,
            copy_elements=True):
        """
        Permet d'ajouter des éléments à partir d'un itérateur d'entité

        Args:
            feature_iter (QgsFeatureIterator): itérateur d'entité à ajouter au réseau 
            field_rtss (_type_): Le champs des entitées contenant le RTSS 
            field_chainage_d (_type_): Le champs des entitées contenant le chainage de début 
            field_chainage_f (_type_): Le champs des entitées contenant le chainage de fin 
            copy_elements (bool, optional): Conserver les éléments de la segmentation intersectée.
        """
        for feat in feature_iter:
            cd, cf = feat[field_chainage_d], feat[field_chainage_f]
            self.addElement(feat[field_rtss], LineSegmentationElement(feat.id()), cd, cf, copy_elements=copy_elements)

    def addFromInterpolation(
        self,
        layer:QgsVectorLayer,
        field_value=None,
        fields_route=[],
        step=10, 
        max_dist=20):
        """
        Permet d'ajouter des éléments au réseau à partir d'une couche.
        L'interpolation est fait en fonction du plus proche voisin. Une distance max peux être spécifier pour 
        limiter l'interpolation. De plus, le paramètre step permet de définir le pas de chainage pour calculer le voisin
        le plus proche.

        Args:
            - layer: Le QgsVectorLayer de la couche à interpoler
            - field_value: Le nom du champ de valeur de la couche
            - fields_route: Une liste de nom de champ dont le 5 première lettre sont le numéro de route à filtrer
            - step: La distance entre chaque point utilisé pour l'interpolation
            - max_dist: La distance maximal pour qu'un objet soit considéré sur la route 
        """
        # Localisation des vitesses
        spatial_index = QgsSpatialIndex(layer.getFeatures(), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        # Pourcourir toutes les modules de référence linéraire des RTSS
        for rtss_seg in self.getReseau().values():
            # Parcourir les chainages des RTSS
            for c in range(int(rtss_seg.chainageDebut().value()), int(rtss_seg.chainageFin().value()), step):
                # Géometrie du point de chainage
                point_geom = rtss_seg.geocoderPointFromChainage(c)
                # Valeurs d'ID et de distance par défault
                feat_id, min_dist = None, max_dist+1
                # Parcourir les ID des entitées à proximité
                for id in spatial_index.nearestNeighbor(point_geom.asPoint(), 5, maxDistance=max_dist):
                    # Vérifier que les numéros de routes sont les mêmes si un champs est spécifié
                    if fields_route == []: pass
                    elif not any([layer.getFeature(id)[f][:5] == rtss_seg.getRoute() for f in fields_route]): continue
                    # Calculer la vrai distances entre les deux geometry
                    distance = layer.getFeature(id).geometry().distance(point_geom)
                    # Conserver la distances la plus petite 
                    if distance < min_dist: feat_id, min_dist = id, distance
                
                # Définir la valeur d'attribut
                if field_value and feat_id: att = {field_value: layer.getFeature(feat_id)[field_value]}
                else: att = {}
                # Vérifier si la valeur de la segmentation au chainage courant est la même que la valeur la plus proche
                value = LineSegmentationElement(feat_id, offset_d=0, attributs=att)
                try: 
                    if rtss_seg.getSegmentation(c).hasElement(value): continue
                except: pass
                # Sinon ajouter une segmentation avec la valeur la plus proche au chainage courant
                rtss_seg.addElement(value, c, rtss_seg.chainageFin(), copy_elements=False)

    def clear(self):
        """ Permet de supprimer l'index du réseau """
        self.reseau = {}

    def getReseau(self): return self.reseau

    def getValues(self): return self.reseau.values()

    def getLinearReference(self, rtss:RTSS)->LinearReferencing:
        """
        Méthode qui permet de retourner le RTSS segmenter

        Args:
            - rtss (RTSS): Le numéro du RTSS 
        """
        return self.reseau.get(RTSS(rtss), None)
    
    def getElements(self, rtss:RTSS, chainage:Chainage)->list[LineSegmentationElement]:
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par un rtss et chainage.

        Args:
            - rtss (str): Le numéro de rtss de la localisation
            - chainage (str/real): La valeur du chainage de la localisation
        """
        # Aller chercher le point de segmentation
        point_segmentation = self.getSegmentation(rtss, chainage)
        if point_segmentation is None: return []
        else: return point_segmentation.getElements()

    def getElementsFromPointRTSS(self, point_rtss:PointRTSS)->list[LineSegmentationElement]:
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par un rtss et chainage.

        Args:
            - point_rtss (PointRTSS): Le PointRTSS avec le RTSS/Chainage de la localisation
        """
        # Aller chercher le point de segmentation
        return self.getElements(point_rtss.getRTSS(), point_rtss.getChainage())
    
    def getElementsFromPoint(self, point):
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par une localisation ponctuelle.

        Args:
            - point (QgsGeometry/QgsPointXY): La localisation du point
        """
        result = self.geocode.getPointOnRTSS(point)
        return self.getElementsFromChainage(result[1], result[2])

    def getSegmentation(self, rtss:RTSS, chainage:Chainage):
        # Aller chercher le RTSS segmenter 
        segment_rtss = self.getLinearReference(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return None
        return segment_rtss.getSegmentation(chainage)

    def isEmpty(self):
        """ Permet de vérifier si le dictionnaire du réseau est vide """
        return self.reseau == {}

    def isRTSSEmpty(self, rtss:RTSS):
        """ Permet de vérifier si le réseau est vide pour le RTSS """
        # Aller chercher le RTSS segmenter 
        segment_rtss = self.getLinearReference(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return None
        return segment_rtss.isEmpty()

    def setReseau(self, reseau:Dict[RTSS, LinearReferencing]):
        """
        Méthode qui permet d'ajouter tout les FeatRTSS au dictionnaire du réseau 

        Args:
            reseau (Dict[RTSS, LinearReferencing]): Le réseau à créer
        """
        # Définir le réseau par défault
        self.reseau = reseau
        # Parcourir tout les RTSS du module de géocodage
        for feat_rtss in self.getListFeatRTSS():
            # Skip les FeatRTSS déjà dans le réseau
            if feat_rtss.getRTSS() in self.reseau: continue
            # Ajouter le FeatRTSS au réseau si il n'était pas présent
            self.reseau[feat_rtss.getRTSS()] = LinearReferencing.fromFeatRTSS(feat_rtss)
        
    def updateSegmentation(self, rtss_seg:LinearReferencing):
        """
        Méthode qui permet de modifier la segmentation d'un RTSS du réseau.

        Args:
            - rtss_seg (LineairReferencing): L'objet qui contient les segmentations sur le RTSS
        """
        if rtss_seg.getRTSS() in self.reseau: self.reseau[rtss_seg.getRTSS()] = rtss_seg
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        