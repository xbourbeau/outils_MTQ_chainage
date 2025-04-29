# -*- coding: utf-8 -*-
import copy
from typing import Union, Dict

from PyQt5.QtCore import QVariant

# Importer les objects du module core de QGIS 
from qgis.core import (QgsCoordinateReferenceSystem, QgsSpatialIndex, QgsFeatureIterator, QgsGeometry,
                       QgsVectorLayer, QgsFeatureRequest, QgsField, QgsVectorLayerUtils, QgsFeature)

from ..geomapping.Chainage import Chainage
from ..geomapping.RTSS import RTSS
from ..geomapping.Geocodage import Geocodage
from ..geomapping.PointRTSS import PointRTSS
from ..geomapping.LineRTSS import LineRTSS

from .LineSegmentationElement import LineSegmentationElement
from .LinearReferencing import LinearReferencing

from ..param import (DEFAULT_NOM_COUCHE_RTSS, DEFAULT_NOM_CHAMP_RTSS,
                     DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, DEFAULT_NOM_CHAMP_FIN_CHAINAGE)


class ReseauSegmenter(Geocodage):
    """ Méthode qui permet de gérer un groupe de RTSS segmentés. """

    def __init__(self, 
                geocode:Geocodage,
                reseau:Dict[RTSS, LinearReferencing]=None):
        """ 
        Initialisation de la class de ReseauSegmenter avec un réseau de Géocodage. 

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
    def fromProject(
        cls,
        layer_name=DEFAULT_NOM_COUCHE_RTSS,
        nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS,
        nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE,
        nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
        precision=0,
        **kwargs):

        geocode = Geocodage.fromProject(
            layer_name=layer_name,
            nom_champ_rtss=nom_champ_rtss,
            nom_champ_long=nom_champ_long,
            nom_champ_chainage_d=nom_champ_chainage_d,
            precision=precision,
            **kwargs)

        return cls(geocode)

    @classmethod
    def fromFields(
        cls,
        geocode:Geocodage,
        layer:QgsVectorLayer,
        fields_value:list[str],
        field_rtss:str,
        field_chainage_d:str,
        field_chainage_f:str,
        filter_request=QgsFeatureRequest()):
        """
        Constructeur qui permet de créer l'objet ReseauSegmenter avec toute les RTSS.
        d'un module de geocodage. Le réseau est segmenter selon le RTSS et chainage début et fin
        d'une couche en entrée. La valeur d'élément est l'identifiant de l'entité de la couche.

        Args:
            - geocode: Module de géocodage
            - layer: Le QgsVectorLayer de la couche
            - fields_value: La liste des noms du champ des valeur de la couche
            - field_rtss: Le nom du champ du RTSS des entitées
            - field_chainage_d: Le nom du champ du chainage de début des entitées
            - field_chainage_f: Le nom du champ du chainage de fin des entitées
            - filter_request (QgsFeatureRequest): Requête pour filtrer la couche en entrée
        """
        reseau = cls(geocode)
        reseau.addFromFields(
            layer.getFeatures(filter_request),
            fields_value,
            field_rtss,
            field_chainage_d,
            field_chainage_f)
        return reseau

    @classmethod
    def fromInterpolation(
        cls, 
        geocode:Geocodage,
        layer:QgsVectorLayer,
        field_value=[],
        fields_route=[],
        step=10, 
        max_dist=20):
        """
        Constructeur qui permet de créer l'objet ReseauSegmenter avec toute les RTSS.
        d'un module de geocodage et ensuite d'ajouter des éléments au réseau à partir d'une couche.

        L'interpolation est fait en fonction du plus proche voisin. Une distance max peux être spécifier pour 
        limiter l'interpolation. De plus, le paramètre step permet de définir le pas de chainage pour calculer le voisin
        le plus proche.

        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau
            - layer: Le QgsVectorLayer de la couche à interpoler
            - field_value: La liste des noms des champs de valeur de la couche
            - fields_route: Une liste de nom de champ dont le 5 première lettre sont le numéro de route à filtrer
            - step: La distance entre chaque point utilisé pour l'interpolation
            - max_dist: La distance maximal pour qu'un objet soit considéré sur la route 
        """
        reseau = cls(geocode)
        reseau.addFromInterpolation(layer, field_value, fields_route, step, max_dist)
        return reseau

    def __str__(self): return f"ReseauSegmenter ({len(self.reseau)} RTSS)"

    def __repr__ (self): return f"ReseauSegmenter ({len(self.reseau)} RTSS)"

    def __getitem__(self, key): 
        try: return self.reseau[RTSS(key)]
        except: raise KeyError(f"Le RTSS ({key}) n'est pas dans le module de geocodage")

    def __len__(self): return len(self.reseau)

    def __iter__ (self): return self.reseau.values().__iter__()

    def __contains__(self, key): return RTSS(key) in self.reseau

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
        segment_rtss = self.get(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return None
        # Ajouter l'élément au réseau
        segment_rtss.addElement(element, chainage_d, chainage_f, copy_elements=copy_elements)

    def addFromFields(self,
            feature_iter:QgsFeatureIterator,
            fields_value,
            field_rtss,
            field_chainage_d,
            field_chainage_f):
        """
        Permet d'ajouter des éléments à partir d'un itérateur d'entité

        Args:
            feature_iter (QgsFeatureIterator): itérateur d'entité à ajouter au réseau 
            fields_value (list of str): La liste des noms des champs qui contient les valeur à ajouter
            field_rtss (str) Le champs des entitées contenant le RTSS 
            field_chainage_d (str): Le champs des entitées contenant le chainage de début 
            field_chainage_f (str): Le champs des entitées contenant le chainage de fin
            copy_elements (bool, optional): Conserver les éléments de la segmentation intersectée.
        """
        # Parourir toutes les entitées de la couche
        for feat in feature_iter:
            # Definir l'objet LinearReferencing
            rtss_seg = self.get(feat[field_rtss])
            # Vérifier si l'objet LinearReferencing est valide
            if rtss_seg is None: continue
            # Ajouter l'id du projet au module de référence linéraire du RTSS
            rtss_seg.addValuesFromFeat(
                feat,
                fields=fields_value,
                field_chainage_d=field_chainage_d,
                field_chainage_f=field_chainage_f)

    def addFromInterpolation(
        self,
        layer:QgsVectorLayer,
        field_value=[],
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
            - field_value: La liste des noms des champs de valeur de la couche
            - fields_route: Une liste de nom de champ dont le 5 première lettre sont le numéro de route à filtrer
            - step: La distance entre chaque point utilisé pour l'interpolation
            - max_dist: La distance maximal pour qu'un objet soit considéré sur la route 
        """
        # Localisation des vitesses
        spatial_index = QgsSpatialIndex()
        # Créer l'index des champs de valeur dans la couche
        field_value = [field_value] if not isinstance(field_value, list) and field_value is not None else field_value
        # Check if a route filter is neaded
        has_route_filter = len(fields_route) > 0
        # Index des QgsGeometry
        geom_index:dict[int, QgsGeometry] = {}
        # Index des attributs à ajouter
        feats_att:dict[int, dict] = {}
        # Index de valeurs de route à considérer
        route_lookup:dict[int, list] = {}
        route_possible = []
        # Parcourir les features de la couche
        for feat in layer.getFeatures():
            # Définir le ID pour la clé
            id = feat.id()
            # Remplir l'index des QgsGeometry
            geom_index[id] = feat.geometry()
            # Remplir l'index des attributs
            feats_att[id] = {field: feat[field] for field in field_value}
            # Remplir l'index des routes
            if has_route_filter:  
                routes = [feat[f][:5] for f in fields_route]
                route_lookup[id] = routes
                route_possible.extend(routes)
            # Ajouter le features
            spatial_index.addFeature(feat)

        # Pourcourir toutes les modules de référence linéraire des RTSS
        for rtss_seg in self:
            l_ref = LinearReferencing(rtss_seg.getRTSS(), rtss_seg.chainageFin(), rtss_seg.geometry())
            # Définir le numéro de la route 
            num_route = rtss_seg.getRoute()
            if has_route_filter:
                # Vérifier si la route est dans la couche
                if not num_route in route_possible: continue
            last_atts = {}
            last_feat_id = None
            # Parcourir les chainages des RTSS
            for c in range(0, int(rtss_seg.chainageFin()), step):
                # Géometrie du point le long du RTSS
                point_geom = rtss_seg.geocoderPointFromChainage(c)
                # Valeurs d'ID et de distance par défault
                feat_id, min_dist = None, max_dist+1
                # Parcourir les ID des entitées à proximité
                for id in spatial_index.nearestNeighbor(point_geom.asPoint(), 5, maxDistance=max_dist):
                    # Check route numbers using cached lookup
                    if has_route_filter:
                        # Vérifier si le feature est pour la bonne route
                        if not num_route in route_lookup[id]: continue
                    # Calculer la vrai distances entre les deux geometry
                    distance = geom_index[id].distance(point_geom)
                    # Conserver la distances la plus petite 
                    if distance < min_dist: feat_id, min_dist = id, distance
                    # Arrêter la recherche si la distance est minimal 
                    if distance == 0: break
                # Arrêter si le features est le même que le précédant
                if last_feat_id == feat_id: continue
                last_feat_id = feat_id
                # Définir la valeur d'attribut
                atts = feats_att[feat_id] if feat_id else {}
                # Vérifier si la valeur de la segmentation au chainage courant est la même que la valeur la plus proche
                if last_atts == atts: continue
                # Sinon ajouter les valeurs 
                l_ref.addValues(chainage_debut=c, copy_elements=False, **atts)
                last_atts = atts 
            rtss_seg.merge(l_ref)

    def addValues(self, rtss:RTSS, chainage_debut:Chainage=None, chainage_fin:Chainage=None, copy_elements=True, **kwargs):
        """
        Méthode qui permet d'ajouter des valeurs entre 2 chainage

        Args:
            rtss (RTSS): Le RTSS sur lequel ajouter les valeurs
            chainage_debut (Chainage): Le chainage de début qui corespond aux valeur. None => le chainage sera celui du RTSS
            chainage_fin (Chainage): Le chainage de fin qui corespond aux valeur. None => le chainage sera celui du RTSS
            copy_elements (bool): Conserver les éléments de la segmentation intersectée

            **kwargs:
            offset_d (float, optional): Le offset de début de l'élément. Defaults to 0.
            offset_f (float, optional): Le offset de fin de l'élément ou None représente une ligne parralèle. Defaults to None.
            intepolate_on_rtss (bool, optional): Indiquateur que le géocodage devrait se faire en suivant le RTSS. Defaults to True.
            Toutes les autres valeurs de l'élément à ajouter

        Returns (bool): True: L'élément avec les valeurs est ajouter False: L'élément n'a pas pu être ajouter
        """
        # Aller chercher le RTSS segmenter 
        segment_rtss = self.get(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return False

        return segment_rtss.addValues(chainage_debut=chainage_debut, chainage_fin=chainage_fin, copy_elements=copy_elements, **kwargs)

    def clear(self):
        """ Permet de supprimer l'index du réseau """
        self.reseau = {}

    def get(self, rtss:RTSS)->LinearReferencing: 
        """ Permet de retourner le LinearReferencing pour un RTSS donnée """
        return self.getLinearReference(rtss)

    def getReseau(self): return self.reseau

    def getValues(self, rtss:RTSS, chainage:Chainage, elem_attribut_name:str, chainage_f:Chainage=None):
        """
        Méthode qui perment de retourner la valeur d'un attibut des l'éléments
        pour un RTSS et chainage donnée.

        Un chainage de fin peux aussi être spécifier pour retourner les valeurs entre 2 chainages

        Args:
            rtss (RTSS): Le RTSS pour lequel retourner les valeurs
            chainage (Chainage): Le chainage à vérifier 
            elem_attribut_name (str): Le nom de l'attribut
            chainage_f (Chainage): Spécifier un chainage de fin
        """
        # Aller chercher le RTSS segmenter 
        segment_rtss = self.get(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return None

        return segment_rtss.getValues(chainage=chainage, elem_attribut_name=elem_attribut_name, chainage_f=chainage_f)

    def getValuesFromPointRTSS(self, point_rtss:PointRTSS, elem_attribut_name:str):
        """
        Méthode qui perment de retourner la valeur d'un attibut des l'éléments
        pour un PointRTSS.

        Args:
            point_rtss (PointRTSS): La localisation sur le RTSS à utiliser
            elem_attribut_name (str): Le nom de l'attribut
        """
        return self.getValues(point_rtss.getRTSS(), point_rtss.getChainage(), elem_attribut_name)

    def getValuesFromLineRTSS(self, line_rtss:LineRTSS, elem_attribut_name:str):
        """
        Méthode qui perment de retourner la valeur d'un attibut des l'éléments
        pour un LineRTSS.

        Args:
            line_rtss (LineRTSS): La localisation sur le RTSS à utiliser
            elem_attribut_name (str): Le nom de l'attribut
        """
        return self.getValues(line_rtss.getRTSS(), line_rtss.startChainage(), elem_attribut_name, line_rtss.endChainage())

    def getValuesFromPoint(self, point, elem_attribut_name:str):
        """
        Méthode qui perment de retourner la valeur d'un attibut des l'éléments
        pour un localisation ponctuel.

        Args:
            point_rtss (QgsGeometry/QgsPointXY): La localisation ponctuelle à utiliser
            elem_attribut_name (str): Le nom de l'attribut
        """
        point_rtss = self.geocoderPointOnRTSS(point)
        return self.getValuesFromPointRTSS(point_rtss, elem_attribut_name)

    def getValuesFromLine(self, line, elem_attribut_name:str):
        """
        Méthode qui perment de retourner la valeur d'un attibut des l'éléments
        pour un localisation linéaire.

        Args:
            point_rtss (QgsGeometry): La localisation linéaire à utiliser
            elem_attribut_name (str): Le nom de l'attribut
        """
        line_rtss = self.geocoderLine(line)
        return self.getValuesFromLineRTSS(line_rtss, elem_attribut_name)

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
        point_rtss = self.geocoderPointOnRTSS(point)
        return self.getElementsFromPointRTSS(point_rtss)

    def getSegmentation(self, rtss:RTSS, chainage:Chainage):
        # Aller chercher le RTSS segmenter 
        segment_rtss = self.getLinearReference(rtss)
        # Vérifier que le RTSS est bien dans le réseau
        if segment_rtss is None: return None
        return segment_rtss.getSegmentation(chainage)

    def info(self, rtss:RTSS, chainage_d:Chainage=None, chainage_f:Chainage=None):
        """
        Méthode qui permet de renvoyer les informations d'un LinearReferencing.

        Args:
            num_rtss (RTSS): Le RTSS du LinearReferencing
            chainage_d (Chainage, optional): Spécifier un chainage de début pour restraindre l'information. Defaults to None.
            chainage_f (Chainage, optional): Spécifier un chainage de fin pour restraindre l'information. Defaults to None.
        """
        lineair_ref = self.get(rtss)
        lineair_ref.info(chainage_d=chainage_d, chainage_f=chainage_f)

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
        
    def createLayer(self, layer_name:str, attributs:dict[str:QVariant]={}):
        """
        Méthode qui permet de créer une couche mémoire avec les attributs du réseau segmenté.

        Args:
            layer_name (str): Le nom de la couche à créer 
            attributs (dict[str:QVariant]): Un dictionnaire des attributs à ajouter. Defaults to {} (toute les attributs).

        Returns (QgsVectorLayer): La couche mémoire avec les attributs du réseau segmenté
        """
        # Create memory layer
        layer = QgsVectorLayer(f"LineString?crs={self.getCrs().authid()}", layer_name, "memory")
        
        # Identifier tous les attributs utilisés si aucun attribut n'est spécifié
        if attributs == {}:
            # Parcourir toutes les LinearReferencing du réseau
            for linear_ref in self:
                # Parcourir toutes les SegmentationPoint du LinearReferencing
                for seg_point in linear_ref:
                    # Parcourir toutes les LineSegmentationElement du SegmentationPoint
                    for elem in seg_point:
                        # Parcourir toutes les attributs du LineSegmentationElement
                        for key, val in elem.getAttributs().items():
                            if key not in attributs:
                                if isinstance(val, float): type_field = QVariant.Double
                                elif isinstance(val, int): type_field = QVariant.Int
                                else: type_field = QVariant.String
                                attributs[key] = type_field
        
        # Définir les champs par défault de la couche
        fields = [
            QgsField("RTSS", QVariant.String),
            QgsField("Chainage_d", QVariant.Int),
            QgsField("Chainage_f", QVariant.Int)]
        # Ajouter les champs des attributs 
        for name, type_ in attributs.items(): fields.append(QgsField(name, type_))
        # Ajouter les champs dans la couche 
        layer.dataProvider().addAttributes(fields)
        # Actualiser la couche avec les champs ajoutés
        layer.updateFields()

        # Définir la liste des features à ajouter dans la couche
        feats = []
        # Créer et ajouter toutes les features de chaque LinearReferencing
        for linear_ref in self: feats.extend(linear_ref.createFeatures(layer))
        
        # Ajouter les features dans la couche
        layer.dataProvider().addFeatures(feats)
        # Retourner la couche
        return layer
                
        