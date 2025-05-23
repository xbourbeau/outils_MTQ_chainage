# -*- coding: utf-8 -*-
import bisect
import copy
from typing import Union, Dict

# Importer les objects du module core de QGIS 
from qgis.core import QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorLayerUtils

from ..geomapping.FeatRTSS import FeatRTSS
from ..geomapping.Chainage import Chainage
from ..geomapping.RTSS import RTSS

from .SegmentationPoint import SegmentationPoint
from .LineSegmentationElement import LineSegmentationElement

class LinearReferencing(FeatRTSS):
    """ Représente un objet FeatRTSS sur lequel il y a une segmentation linéaire. """

    __slots__ = ("num_rts", "chainage_d", "chainage_f", "attributs", "geom", "segmentation_points", "keep_offset")
    
    def __init__(self,
                 num_rtss:Union[RTSS, str], 
                 chainage_f:Union[Chainage, str, float, int],
                 geometry:QgsGeometry,
                 list_segmentation_points=[], 
                 keep_offset=False,
                 **kwarg):
        # Dictionnaire des segmentations sur le RTSS. La clé est la valeur du chainage et la 
        self.segmentation_points:Dict[Chainage, SegmentationPoint] = {}
        FeatRTSS.__init__(self, num_rtss, chainage_f, geometry, **kwarg)
        # Ajouter les segmentations existantes
        self.addSegmentations(list_segmentation_points)
        self.setKeepOffset(keep_offset)
    
    @classmethod
    def fromFeatRTSS(cls, feat_rtss:FeatRTSS, list_segmentation_points=[]):
        """ Construire un objet LinearReferencing à partir d'un objet FeatRTSS """
        return cls(feat_rtss.getRTSS(), feat_rtss.chainageFin(), feat_rtss.geometry(), list_segmentation_points)
    
    @classmethod
    def fromGeometry(cls, id, geometry:QgsGeometry, list_segmentation_points=[]):
        """
        Construire un objet LinearReferencing à partir d'une geometry linéaire.

        Args:
            - id (str/int): Un identifiant qui prendra la place du RTSS (pas nécéssairement un RTSS) Ex: 1 => 00000000000001
            - geometry (QgsGeometry): La géométrie linéaire à utiliser 
            - list_segmentation_points (list): Liste des points de segmentation à ajouter
        """
        return cls(str(id).zfill(14), 0, geometry.length(), list_segmentation_points=list_segmentation_points)

    def __str__(self): return f"{super().__str__()}: {len(self)} points de segmentation"

    def __repr__(self): return f"LinearReferencing {self.__str__()}"
    
    def __iter__ (self): return sorted(list(self.segmentation_points.values()), key=lambda p: p.getChainage()).__iter__()

    def __getitem__(self, index): return self.segmentation_points[Chainage(index)]

    def __contains__(self, key): return Chainage(key) in self.segmentation_points

    def __len__(self): return len(self.segmentation_points)

    def __deepcopy__(self, memo):
        new_obj = self.__class__.__new__(self.__class__)

        # Add the new object to the memo dictionary to avoid infinite recursion
        memo[id(self)] = new_obj

        # Deep copy all the attributes
        for slot in self.__slots__:
            v = getattr(self, slot)
            # Use the copy method for QgsGeometry objects
            if isinstance(v, QgsGeometry): setattr(new_obj, slot, QgsGeometry(v))
            else: setattr(new_obj, slot, copy.deepcopy(v, memo))

        return new_obj

    def addElement(self, element:LineSegmentationElement, chainage_debut=None, chainage_fin=None, copy_elements=True):
        """
        Méthode qui permet d'ajouter un élément sur le RTSS
        
        Args:
            - element (LineSegmentationElement): Élement à ajouter
            - chainage_debut (Chainage): Chainage de début de l'élément. None => le chainage sera celui du RTSS
            - chainage_fin (Chainage): Chainage de fin de l'élément. None => le chainage sera celui du RTSS
            - copy_elements (bool): Conserver les éléments de la segmentation intersectée
        """
        # Ajouter un point de segmentation au chainage de début s'il y en a pas déjà une
        try: 
            if chainage_debut is None: chainage_debut = self.chainageDebut()
            self.addSegmentationFromChainage(chainage_debut, copy_elements=copy_elements)
        except NameError: pass
        # Ajouter un point de segmentation au chainage de fin s'il y en a pas déjà une
        try: 
            if chainage_fin is None: chainage_fin = self.chainageFin()
            self.addSegmentationFromChainage(chainage_fin, copy_elements=copy_elements)
        except NameError: pass
        # Ajouter l'élément pour toutes les points de segmentations sur le RTSS
        for chainage in self.getListChainage(start=chainage_debut, end=chainage_fin):
            self[chainage].addElement(element)

    def addEnd(self, chainage):
        """ Méthode qui permet d'ajouter une point de segmentation qui représente une fin d'information. """
        self.addSegmentationFromChainage(chainage, copy_elements=False)

    def addSegmentation(self, segmentation_point:SegmentationPoint, copy_elements=False):
        """
        Méthode qui permet d'ajouter un point de segmentation sur le RTSS
        
        Args:
            - segmentation_point (SegmentationPoint): Le point de segmentation ou chainage à ajouter
            - copy_elements (bool): Conserver les éléments de la segmentation intersectée
        """
        # Vérifier que le chainage du point est sur le RTSS 
        if not self.isSegmentationOnRTSS(segmentation_point):
            raise NameError(f"Le {segmentation_point.__repr__()} n'est pas sur le RTSS {self.value(formater=True)}")
        # Vérifier que le chainage est unique
        if not self.isSegmentationUnique(segmentation_point):
            raise NameError(f"Le {segmentation_point.__repr__()} est deja sur le RTSS {self.value(formater=True)}")
        
        # Ajouter la segmentation au RTSS
        self.segmentation_points[segmentation_point.getChainage()] = segmentation_point
        if copy_elements:
            # Définir la segmentation précédant 
            previous_segmentation = self.getPreviousSegmentation(segmentation_point)
            # Copier les éléements de la segmentation précédante
            if previous_segmentation: segmentation_point.setElements(copy.deepcopy(previous_segmentation.getElements()))
        
        self.updateElementsOffsets(segmentation_point, update_current=copy_elements)
    
    def addSegmentationFromChainage(self, chainage, copy_elements=False, **kwargs):
        """ Méthode qui permet d'ajouter un point de segmentation sur le RTSS à partir d'un chainage. """
        segmentation_point = self.createSegmentation(chainage, **kwargs)
        self.addSegmentation(segmentation_point, copy_elements=copy_elements)

    def addSegmentations(self, list_segmentation_points):
        """
        Méthode qui permet d'ajouter plusieurs points de segmentation sur le RTSS
        
        Args:
            - list_segmentation_points (list): Liste de SegmentationPoint
        """
        for point in list_segmentation_points: self.addSegmentation(point)

    def addSegmentationsFromChainage(self, list_chainage):
        """
        Méthode qui permet d'ajouter plusieurs points de segmentation sur le RTSS à partir
        d'une list de chainage.
        
        Args:
            - list_chainage (list): Liste de chainages
        """
        for chainage in list_chainage: self.addSegmentationFromChainage(chainage)

    def addValues(self, chainage_debut=None, chainage_fin=None, copy_elements=True, **kwargs):
        """
        Méthode qui permet d'ajouter des valeurs entre 2 chainage

        Args:
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
        elem = LineSegmentationElement(**kwargs)
        if elem.isEmpty(): return False
        self.addElement(elem, chainage_debut, chainage_fin, copy_elements=copy_elements)
        return True
    
    def addValuesFromFeat(
            self,
            feat:QgsFeature,
            fields:list[str],
            field_chainage_d:str=None,
            field_chainage_f:str=None,
            field_offset_d:str=None,
            field_offset_f:str=None,
            copy_elements=True,
            **kwargs):
        """
        Méthode qui permet d'ajouter des valeurs à partir d'un entité

        Args:
            feat (QgsFeature): L'entitée à ajouter
            fields (list[str]): Liste des champs des valeurs de l'entité
            field_chainage_d (str, optional): Nom du champs qui contients le chainage de début. Defaults to None.
            field_chainage_f (str, optional): Nom du champs qui contients le chainage de fin. Defaults to None.
            field_offset_d (str, optional): Nom du champs qui contients le offset de début. Defaults to None.
            field_offset_f (str, optional): Nom du champs qui contients le offset de fin. Defaults to None.
            copy_elements (bool, optional): Conserver les éléments des segmentations intersectées. Defaults to True.

            **kwargs:
            offset_d (float, optional): Le offset de début de l'élément. Defaults to 0.
            offset_f (float, optional): Le offset de fin de l'élément ou None représente une ligne parralèle. Defaults to None.
            intepolate_on_rtss (bool, optional): Indiquateur que le géocodage devrait se faire en suivant le RTSS. Defaults to True.
            Toutes les autres valeurs de l'élément à ajouter

        Returns (bool): True: L'élément avec les valeurs est ajouter False: L'élément n'a pas pu être ajouter
        """
        
        has_chainage_d = "chainage_debut" in kwargs or field_chainage_d is not None
        has_chainage_f = "chainage_fin" in kwargs or field_chainage_f is not None
        has_offset_d = "offset_d" in kwargs or field_offset_d is not None
        has_offset_f = "offset_f" in kwargs or field_offset_f is not None
        
        if not all([has_chainage_d, has_chainage_f, has_offset_d, has_offset_f]):
            line_rtss = self.geocoderInverseLine(feat.geometry())
            if not has_chainage_d: cd = line_rtss.startChainage()
            if not has_chainage_f: cf = line_rtss.endChainage()
            if not has_offset_d: od = line_rtss.startOffset()
            if not has_offset_f: of = line_rtss.endOffset()

        def getValue(arg, field):
            if arg in kwargs: return kwargs[arg]
            else: return feat[field]
        
        if has_chainage_d: cd = getValue("chainage_debut", field_chainage_d)
        if has_chainage_f: cf = getValue("chainage_fin", field_chainage_f)
        if has_offset_d: od = getValue("offset_d", field_offset_d)
        if has_offset_f: of = getValue("offset_f", field_offset_f)

        vals = {field:feat[field] for field in fields}

        return self.addValues(chainage_debut=cd, chainage_fin=cf, copy_elements=copy_elements, offset_d=od, offset_f=of, **vals, **kwargs)            

    def chainageExists(self, chainage): 
        """ Méthode qui permet de vérifier si le chainage est unique dans le RTSS """
        return Chainage(chainage) in self.segmentation_points
    
    def createFeatures(self, layer:QgsVectorLayer) -> list[QgsFeature]:
        """
        Crée une liste d'entités linéaires (QgsFeature) correspondant aux segments du RTSS.
 
        Pour chaque point de segmentation (sauf le dernier) possédant des éléments,
        la géométrie de la ligne est générée à l'aide de la méthode geocoderElement.
        Les attributs sont automatiquement ajoutés sans avoir à être explicitement listés,
        et les attributs à None sont ignorés.
 
        Args:
            layer (QgsVectorLayer): La couche vectorielle dans laquelle les entités seront créées.

        Returns:
            list[QgsFeature]: Liste des entités linéaires créées.
        """
        # Définir la liste des features à créer 
        features = []
        # Définir le dictionnaire des attributs de la couche
        dict_attrs = {i:field.name() for i, field in enumerate(layer.fields())}
        # Créer les entités avec uniquement les champs utilisés
        for seg_point in self:
            # Skip si le point de segmentation est une fin
            if seg_point.isEnd(): continue

            # Définir le chainage suivant pour la ligne 
            next_chainage = self.getNextChainage(seg_point)
            if next_chainage is None: continue

            # Parcourir toutes les LineSegmentationElement du SementationPoint
            for elem in seg_point:
                # Géocoder la géométrie de l'élément
                geom = self.geocoderElement(seg_point, elem, interpolate_on_rtss=True)
                # Dictinaires de attributs du features à créer
                atts = {}
                # Parcourir les champs de la couche 
                for idx, name in dict_attrs.items():
                    # Vérifier si l'élément possède une valeur pour le champ
                    value = elem.getAttribut(name)
                    # Ajouter la valeur de l'élément seulement si elle est non-nulles
                    if value is not None: atts[idx] = value
                # Définir l'attribut du RTSS
                atts[0] = self.getRTSS().valueFormater()
                # Définir l'attribut du Chainage de début
                atts[1] = seg_point.getChainage().value(precision=0)
                # Définir l'attribut du Chainage de fin
                atts[2] = next_chainage.value(precision=0)
                # Créer et ajouter le feature à la liste
                features.append(QgsVectorLayerUtils.createFeature(layer, geom, atts))
        # Retourner la liste des feautures
        return features

    def createSegmentation(self, chainage, list_elements=[], **kwargs):
        """
        Méthode qui permet de créer un objet SegmentationPoint associer au RTSS.
        Le chainage est assuré d'être sur le RTSS
        """
        return SegmentationPoint(
            self.getRTSS(),
            self.getChainageOnRTSS(chainage),
            list_elements,
            **kwargs)

    def info(self, chainage_d:Chainage=None, chainage_f:Chainage=None):
        """ Méthode qui permet de print dans la consoles les informations du LinearReferencing """
        print(self.__str__())
        for point_seg in self.getSegmentations(chainage_d=chainage_d, chainage_f=chainage_f):
            if point_seg.isEnd(): continue
            print(f"{point_seg.getChainage().formaterChainage()} -> {self.getNextChainage(point_seg).formaterChainage()}")
            point_seg.infoAttributs()
            point_seg.infoElements()
            print()

    def geocoderElement(self, segmentation_point:SegmentationPoint, elem:LineSegmentationElement, interpolate_on_rtss=True):
        """
        Permet de géocoder une element linéaire d'une segmentation
        
        Args:
            - segmentation_point (SegmentationPoint): Le point de segmentation
            - elem (LineSegmentationElement): L'élément à géocoder
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points
        """
        return self.geocoderLineFromChainage(
            chainages=[segmentation_point.getChainage(), self.getNextChainage(segmentation_point)],
            offsets=[elem.getOffsetDebut(), elem.getOffsetFin()],
            interpolate_on_rtss=interpolate_on_rtss)

    def geocoderSegmentation(self, chainage):
        """ Permet de géocoder le point de segmentation sur le RTSS """
        segmentation_point = self.getSegmentation(chainage)
        return self.geocoderPoint(segmentation_point)

    def getClosestSegmentation(self, chainage, dist_max=-1):
        """
        Méthode qui permet de retourner le point de segmentation le plus proche du chainage.
        Le point de segmentation n'est pas nécéssairement la segmentation au chainage, mais 
        seulement le point le plus proche.
        
        Args:
            - chainage (str/real): Chainage à vérifier
            - dist_max (int): Distance maximun de la segmentation la plus proche
        """
        # Retourner None pour des segmentations vide
        if self.isEmpty(): return None
        # Dernière segmentation la plus proche et sa distance
        last_point, last_dist = None, 100000000
        # Définir s'il faut parcourir les points de segmentation dans le sense inverse
        nbr_point = len(self)
        if nbr_point > 10: reverse = chainage > list(self.__iter__())[int(nbr_point/2)].getChainage()
        else: reverse = False
        # Parcourir les points de segmentation
        for point_segmentation in self.getSegmentations(reverse=reverse):
            # Calculer la distance du point avec le chainage chercher
            dist = abs(point_segmentation.getChainage() - chainage)
            # Arrêter la boucle quand la distance entre les deux devient plus grande
            if dist > last_dist: break
            # Conserver la dernière segmentation la plus proche et sa distance
            last_point, last_dist = point_segmentation, dist
        # Retourner rien si une distance max est défini et le point le plus proche est plus loin que la distance
        if last_dist > dist_max and dist_max != -1: return None
        return last_point

    def getElements(self, chainage:Chainage)->list[LineSegmentationElement]:
        """ Permet de retourner la liste des éléments présent au chainage. """
        point_seg = self.getSegmentation(chainage)
        if point_seg is None: return []
        return point_seg.getElements()

    def getListChainage(self, start=None, end=None):
        """
        Méthode qui permet de retourner une liste de toutes les chainages des segmentations 
        entre un chainage de début et fin. Le début est inclus et le fin n'est pas inclus.
        
        Args:
            - start (str/real): Le chainage de début de la recherche
            - end (str/real): Le chainage de fin de la recherche qui n'est pas inclus
        """
        # Retourner la liste de toutes les chainages des segmentations du RTSS si aucun début ou fin n'est défini
        if start is None and end is None: return sorted(list(self.segmentation_points.keys()))
        # Définir le chainage de début comme le début du RTSS s'il n'était pas défini
        if start is None: start, end = self.chainageDebut(), Chainage(end)
        # Définir le chainage de fin comme la fin du RTSS s'il n'était pas défini
        elif end is None: start, end = Chainage(start), self.chainageFin()
        else: start, end = Chainage(start), Chainage(end)
        # Retourner toutes les chainages entres le début et la fin des chainage
        return sorted([chainage for chainage in self.segmentation_points.keys() if chainage >= start and chainage < end])
    
    def getNextSegmentation(self, segmentation_point:SegmentationPoint, check_end=False):
        """
        Méthode qui permet de retourner le prochain Segmentation d'un autre SegmentationPoint sur le RTSS.
        
        Args:
            - segmentation_point(SegmentationPoint): La segmentation à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        # Retourner le point de segmentation si il n'a aucun éléments (il est un fin)
        if segmentation_point.isEmpty() and check_end: return segmentation_point
        # Définir la liste des chainages
        list_chainages = self.getListChainage()
        # Définir la position du chainage suivant sur la liste des chainages
        pos = list_chainages.index(segmentation_point.getChainage()) + 1
        # Retourner None si la segmentation est la dernier de la liste
        if pos == len(list_chainages): return segmentation_point
        # Retrouner la segmentation suivant
        return self.segmentation_points.get(list_chainages[pos], segmentation_point)
        
    def getNextChainage(self, segmentation_point:SegmentationPoint, check_end=False):
        """
        Méthode qui permet de retourner le prochain chainage d'un SegmentationPoint sur le RTSS.
        
        Args:
            - segmentation_point(SegmentationPoint): La segmentation à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        next_segmentation = self.getNextSegmentation(segmentation_point, check_end=check_end)
        if next_segmentation == segmentation_point: return None
        return next_segmentation.getChainage() 
    
    def getPreviousSegmentation(self, segmentation_point:SegmentationPoint, check_end=False):
        """
        Méthode qui permet de retourner la segmentation précédant sur le RTSS 
        d'un SegmentationPoint.
        
        Args:
            - segmentation_point(SegmentationPoint): La segmentation à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        # Définir la liste des chainages
        list_chainages = self.getListChainage()
        # Définir la position du chainage précédant sur la liste des chainages
        pos = list_chainages.index(segmentation_point.getChainage()) - 1
        # Retourner None si la segmentation est la dernier de la liste
        if pos == -1: return segmentation_point
        # Définir la segmentation précédant
        previous_segmentation = self.segmentation_points.get(list_chainages[pos], segmentation_point)
        # Retourner le point de segmentation en entré si le précédant n'a pas d'éléments
        if previous_segmentation.isEmpty() and check_end: return segmentation_point
        # Sinon retourner le point de segmentation précédant
        else: return previous_segmentation
    
    def getPreviousChainage(self, segmentation_point:SegmentationPoint, check_end=False):
        """
         Méthode qui permet de retourner le chainage d'un SegmentationPoint précédant d'un 
         autre SegmentationPoint sur le RTSS.
        
        Args:
            - segmentation_point(SegmentationPoint): La segmentation à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        previous_segmentation = self.getPreviousSegmentation(segmentation_point, check_end=check_end)
        if previous_segmentation == segmentation_point: return None
        return previous_segmentation.getChainage()
    
    def getSegmentation(self, chainage):
        """
        Méthode qui permet de retourner un point de segmentation du RTSS a partir d'un chainage
        
        Args:
            - value (str/real): La valeur à rechercher
        """
        chainage = self.getChainageOnRTSS(chainage)
        # Retourner le point de segmentation exact seulement
        if chainage in self.segmentation_points: segmentation_point = self[chainage]
        # Retourner le point de segmentation d'un element
        else:
            # Définir la listes des chainages sur le RTSS
            chainages = self.getListChainage()
            # Trouver l'index du point de segmentation au chainage avant ou égale 
            index = bisect.bisect_right(chainages, chainage)
            # Vérifier si l'index est valide
            if index <= 0 or index == len(chainages): return None
            # Retourner le point de segmentation à l'index
            segmentation_point = self[chainages[index - 1]]
            # Retourner None si le point de segmentation avant est une fin
            if segmentation_point.isEmpty(): return None
        
        return segmentation_point
    
    def getSegmentations(self, chainage_d:Chainage=None, chainage_f:Chainage=None, reverse=False):
        """ Permet de retourner un iterateur sur les points de segmentations """
        # Liste completes des points de segmentation si aucun chainage n'est spécifié
        if chainage_d is None and chainage_f is None: list_points = list(self.__iter__())
        else:
            # Liste des points de segmentation à retourner 
            list_points = []
            # Aller chercher un point de segmentation au chainage de début
            first_pt = self.getSegmentation(chainage_d)
            # Vérifier si on point de segmentation à été trouvé
            if not first_pt is None: 
                # Ajouter le point de segmentation s'il n'est pas une fin
                if not first_pt.isEnd(): list_points.append(first_pt)
            # Parcourir les chainages des points de segmentation présent entre les 2 chainage
            for chainage in self.getListChainage(start=chainage_d, end=chainage_f):
                # Aller chercher un point de segmentation au chainage
                pt = self.getSegmentation(chainage)
                # Ajouter le point de segmentation s'il n'est pas une fin et qu'il n'est pas déjà dans la liste
                if pt not in list_points and not pt.isEnd(): list_points.append(pt)
        
        # Inverser la ligne si indiqué en paramêtre
        if reverse: list_points.reverse()
        # Retourner l'itérateur des points de segmentation
        return list_points.__iter__()

    def getSegmentationByAttribute(self, attribut, value):
        """ Méthode qui permet de retourner la liste des points de segmentation avec une valeur d'attribut """
        return [pt for pt in self.getSegmentations() if pt.getAttribut(attribut) == value] 
    
    def getAllValues(self, elem_attribut_name):
        """ Permet de retourner toutes les valeurs d'une element sur le RTSS """
        return self.getValues(self.chainageDebut(), elem_attribut_name, self.chainageFin())

    def getValues(self, chainage:Chainage, elem_attribut_name:str, chainage_f:Chainage=None):
        """
        Méthode qui perment de retourner la valeur d'un attibut des l'éléments
        pour le chainage donnée.
        
        Un chainage de fin peux aussi être spécifier pour retourner les valeurs entre 2 chainages.

        Args:
            chainage (Chainage): Le chainage à vérifier 
            elem_attribut_name (str): Le nom de l'attribut
            chainage_f (Chainage): Spécifier un chainage de fin
        """
        # Définir le point de segmentation
        if chainage_f is None: points = [self.getSegmentation(chainage)]
        else: points = self.getSegmentations(chainage_d=chainage, chainage_f=chainage_f)
        
        values = []
        # Étendre la liste des valeurs avec les valeurs des éléments du point de segmentation
        for pt in points: values.extend(pt.getValues(elem_attribut_name))

        # Retourner la valeur de l'élément
        return list(set(values))

    def getUniqueValue(self, chainage:Chainage, elem_attribut_name:str):
        """
        Méthode qui perment de retourner la valeur d'un attibut unique de l'élément
        pour le chainage donnée.

        Args:
            chainage (Chainage): Le chainage à vérifier 
            elem_attribut_name (str): Le nom de l'attribut unique 
        """
        # Définir le point de segmentation
        point_segmentation = self.getSegmentation(chainage)
        # Retourner la valeur de l'élément
        return point_segmentation.getUniqueValue(elem_attribut_name)

    def hasNextSegmentation(self, segmentation_point:SegmentationPoint, check_end=True):
        """ Méthode qui permet de verifier si une segmentation à une segmentation suivant sur le RTSS """ 
        return segmentation_point != self.getNextSegmentation(segmentation_point, check_end=check_end)
     
    def hasPreviousSegmentation(self, segmentation_point:SegmentationPoint, check_end=True):
        """ Méthode qui permet de verifier si une segmentation à une segmentation précédant sur le RTSS """
        return segmentation_point != self.getPreviousSegmentation(segmentation_point, check_end=check_end)
    
    def isEmpty(self):
        """ Méthode qui permet de vérifier si la segmentation du RTSS est vide """
        return self.segmentation_points == {}

    def isSegmentationOnRTSS(self, segmentation_point:SegmentationPoint):
        """ Permet de vérifier si un point de segmentation est sur le rtss """
        return (self.isChainageOnRTSS(segmentation_point.getChainage()) and
            segmentation_point.getRTSS() == self.getRTSS())

    def isSegmentationUnique(self, segmentation_point:SegmentationPoint):
        """ Permet de vérifier qu'un SegmentationPoint est unique sur le RTSS """
        return not segmentation_point.getChainage() in self

    def keepOffset(self): return self.keep_offset

    def merge(self, lineaire_ref):
        """
        Méthode qui permet d'ajouter les elements d'un autre LinearReferencing au 
        LinearReferencing courant.

        Args:
            - lineaire_referencing(LinearReferencing) = Le LinearReferencing qui contient les éléments à ajouter
        """
        if lineaire_ref.getRTSS() != self.getRTSS(): return None
        # Parcourir les points de segmentation du LinearReferencing à combiner
        for seg_pt in lineaire_ref:
            # Parcourir les éléments du point de segmentation
            for elem in seg_pt.getElements():
                self.addElement(elem, chainage_debut=seg_pt.getChainage(), chainage_fin=lineaire_ref.getNextChainage(seg_pt))

    def moveSegmentation(self, segmentation_point:SegmentationPoint, new_chainage):
        """ 
        Méthode qui permet de déplacer une segmentation à un chainage différent
        
        Args:
            - segmentation_point(SegmentationPoint): Le point de segmentation à déplacer
            - new_chainage(real/str): Le nouveau chainage de la segmentation
        """
        # Vérifier que le nouveau chainage n'existe pas et qu'il est sur le RTSS 
        if self.chainageExists(new_chainage) or not self.isChainageOnRTSS(new_chainage): return False
        new_segmentation_point = segmentation_point.copy()
        # Modifier le chainage de la segmentation pour le nouveau chainage
        new_segmentation_point.setChainage(new_chainage)
        # Retirer la segmentation
        self.removeSegmentation(segmentation_point)
        # Ajouter la nouvelle segmentation
        self.addSegmentation(new_segmentation_point)
        return True

    def updateElementsOffsets(self, segmentation_point:SegmentationPoint, update_current=True, update_previous=True):
        """
        Permet de mettre à jour les offsets des éléments touchée par la modification
        d'un point de segmentation.

        Args:
            segmentation_point (SegmentationPoint): Le point de segmentation modifiée
            update_current (bool, optional): Mettre a jour les offsets des éléments du SegmentationPoint. Defaults to True.
            update_previous (bool, optional): Mettre a jour les offsets des éléments du point précédant. Defaults to True.
        """
        if self.keepOffset(): return None
        # Définir la segmentation précédant 
        previous_segmentation = self.getPreviousSegmentation(segmentation_point, check_end=True)
        next_chainage = self.getNextChainage(segmentation_point, check_end=False)

        if update_previous:
            for elem in previous_segmentation.getElements():
                if elem.isParallel(): continue
                new_offset = self.interpolateOffsetAtChainage(
                    chainage=segmentation_point.getChainage(),
                    chainage_d=previous_segmentation.getChainage(),
                    chainage_f=next_chainage,
                    offset_d=elem.getOffsetDebut(),
                    offset_f=elem.getOffsetFin())
                elem.setOffsetFin(new_offset)
        if update_current:  
            for elem in segmentation_point.getElements():
                if elem.isParallel(): continue
                new_offset = self.interpolateOffsetAtChainage(
                    chainage=segmentation_point.getChainage(),
                    chainage_d=previous_segmentation.getChainage(),
                    chainage_f=next_chainage,
                    offset_d=elem.getOffsetDebut(),
                    offset_f=elem.getOffsetFin())
                elem.setOffsetDebut(new_offset)

    def updateValues(self, chainage_debut=None, chainage_fin=None, **kwargs):
        """ 
        Méthode qui permet de mettre à jour les valeurs d'un attribut des éléments
        contenues entre les 2 chainages.
        """
        if chainage_debut is None: chainage_debut = self.chainageDebut()
        if chainage_fin is None: chainage_fin = self.chainageFin()
        # Ajouter l'élément pour toutes les points de segmentations sur le RTSS
        for pt_seg in self.getSegmentations(chainage_d=chainage_debut, chainage_f=chainage_fin):
            attribute_exists=False
            for elem in pt_seg.getElements():
                for att_name in elem.getAttributsName():
                    if att_name in kwargs:
                        elem.setAttribut(att_name, kwargs[att_name])
                        attribute_exists=True
            if not attribute_exists:
                pt_seg.addElement(LineSegmentationElement(**kwargs))

    def removeSegmentation(self, segmentation_point:SegmentationPoint, check_end=False):
        """
        Méthode qui permet de supprimer une segmentation du RTSS
        
        Args:
            - segmentation_point(SegmentationPoint): Le point de segmentation à supprimer
            - check_end (bool): Considérer les points de segmentation vide
        """
        if (self.hasPreviousSegmentation(segmentation_point) and
            check_end and segmentation_point.isEmpty() and
            not self.hasNextSegmentation(segmentation_point, check_end=False)): return False
        
        previous_segmentation = self.getPreviousSegmentation(segmentation_point, check_end=True)
        self.segmentation_points.pop(segmentation_point.getChainage(), False)
        
        # Update offsets
        if previous_segmentation and not self.keepOffset():
            for elem in previous_segmentation.getElements():
                if elem.isParallel(): continue
                new_offset = self.interpolateOffsetAtChainage(
                    chainage=self.getNextChainage(previous_segmentation),
                    chainage_d=previous_segmentation.getChainage(),
                    chainage_f=segmentation_point.getChainage(),
                    offset_d=elem.getOffsetDebut(),
                    offset_f=elem.getOffsetFin())
                elem.setOffsetFin(new_offset)

        return True
        
    def setKeepOffset(self, keep_offset:bool):
        self.keep_offset = keep_offset 