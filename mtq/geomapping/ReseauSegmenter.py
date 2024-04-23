# -*- coding: utf-8 -*-
from qgis.core import QgsSpatialIndex, QgsFeatureRequest, QgsFeature
from typing import Union, Dict
from .imports import *
# Importer les objects du module core de QGIS 
from qgis.core import (QgsCoordinateReferenceSystem, QgsSpatialIndex, QgsFeatureIterator,
                       QgsVectorLayer)

from ..param import (DEFAULT_NOM_CHAMP_RTSS, DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                    DEFAULT_NOM_CHAMP_FIN_CHAINAGE)

class ReseauSegmenter(Geocodage):
    """ Méthode qui permet de gérer un groupe de RTSS segmentés. """

    def __init__(self, 
                rtss_features:QgsFeatureIterator,
                crs:QgsCoordinateReferenceSystem,
                nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS,
                nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE,
                nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                precision=0,
                reseau:Dict[RTSS, LinearReferencing]={},
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
        self.reseau = reseau
        Geocodage.__init__(
            self,
            rtss_features=rtss_features,
            crs=crs,
            nom_champ_rtss=nom_champ_rtss,
            nom_champ_long=nom_champ_long,
            nom_champ_chainage_d=nom_champ_chainage_d,
            precision=precision,
            **kwargs)
    
    @classmethod
    def fromGeocodage(cls, geocode, reseau:Dict[RTSS, LinearReferencing]={}):
        """
        Constructeur de l'objet ReseauSegmenter

        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau 
            - reseau (dict): Dictionnaire des objet de LinearReferencing
        """
        #reseau_segmenter = cls.fromSelf(geocode)
        reseau_segmenter = cls.fromSelf(geocode)
        reseau_segmenter.setModuleGeocodage(geocode)
        return reseau_segmenter
        #reseau_segmenter.reseau = reseau
        #return reseau_segmenter

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
            # Ajouter l'id du projet au module de référence linéraire du RTSS
            rtss_seg.addElement(feat.id(), cd, cf)
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

    def setModuleGeocodage(self, geocode:Geocodage):
        """
        Méthode qui permet de définir le module de geocodage sur lequel baser le réseau.

        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau
        """
        self.geocode = geocode
        self.reseau:Dict[RTSS, LinearReferencing] = {feat_rtss.getRTSS(): LinearReferencing.fromFeatRTSS(feat_rtss) for feat_rtss in self.geocode.getListFeatRTSS()}
    
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

    def getReseau(self): return self.reseau

    def getValues(self): return self.reseau.values()

    def addRTSSSegmenter(self, rtss_seg, overide=False):
        """
        Méthode qui permet d'ajouter un RTSS segmenté au réseau.

        Args:
            - rtss_seg (LineairReferencing): L'objet qui contient les segmentations sur le RTSS 
            - overide (bool): Effacer le RTSS existant
        """
        if overide or not rtss_seg.getRTSS() in self.reseau:
            self.reseau[rtss_seg.getRTSS()] = rtss_seg

    def getRTSSSegmenter(self, rtss):
        """
        Méthode qui permet de retourner le RTSS segmenter

        Args:
            - rtss (str): Le numéro du RTSS 
        """
        return self.reseau.get(RTSS(rtss), None)
    
    def getElementsFromChainage(self, rtss, chainage)->list[LineSegmentationElement]:
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par un rtss et chainage.

        Args:
            - rtss (str): Le numéro de rtss de la localisation
            - chainage (str/real): La valeur du chainage de la localisation
        """
        rtss_seg = self.getRTSSSegmenter(rtss)
        if rtss_seg is None: return None
        point_segmentation = rtss_seg.getSegmentation(chainage)
        if point_segmentation: return point_segmentation.getElements()
        else: return None
    
    def getElementsFromPoint(self, point):
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par une localisation ponctuelle.

        Args:
            - point (QgsGeometry/QgsPointXY): La localisation du point
        """
        result = self.geocode.getPointOnRTSS(point)
        return self.getElementsFromChainage(result[1], result[2])
        


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        