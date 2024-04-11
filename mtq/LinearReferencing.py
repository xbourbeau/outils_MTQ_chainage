# -*- coding: utf-8 -*-
import bisect
from .format import verifyFormatChainage, verifyFormatRTSS
from .geocodage import geocodage, featRTSS
from qgis.core import QgsSpatialIndex, QgsFeatureRequest

class SegmentationPoint:
    """
    Objet représentant une segmentation des éléments réseau sur un RTSS.
    Une segmentation possède un chainage unique sur le RTSS et contient une liste des éléments
    contenue au chainage. 
    Une segmentation peut également contenir des attributs.
    """
    __slots__ = ("chainage", "list_elements", "dict_attributs")
    
    def __init__(self, chainage, elements=[], attributs={}):
        """
        Initialisation d'un objet SegmentationPoint

        Args:
            - chainage (réel/str): Le chainage du point de segmentation
            - elements (list): La liste des éléments contenu dans le point
            - attributs (dict): Attributs pouvant caractériser le point de segmentation
        """
        self.chainage = verifyFormatChainage(chainage)
        self.setElements(elements)
        self.dict_attributs = {}
        self.dict_attributs.update(attributs)
    
    def __str__(self):  return f"{self.chainage}: {self.list_elements}"
        
    def __repr__(self): return f"SegmentationPoint {self.chainage}: {self.list_elements}"
    
    def copy(self): return SegmentationPoint(self.chainage, elements=self.list_elements, attributs=self.dict_attributs)
    
    def addElement(self, new_element): 
        """ Méthode qui permet d'ajouter un élément a la segmentation """
        self.list_elements.append(new_element)
    
    def addElements(self, new_elements):
        """ Méthode qui permet d'ajouter plusieurs éléments a la segmentation """
        self.list_elements.extend(new_elements)
    
    def getAttribut(self, attribut_name):
        """ Méthode qui permet de retourner une des valeurs d'attribut """
        return self.dict_attributs.get(attribut_name, None)
    
    def getChainage(self):
        """ Méthode qui permet de retourner le chainage du point de segmentation """
        return self.chainage
    
    def getElements(self): 
        """ Méthode qui permet de retourner les éléments associé au point de segmentation """
        return self.list_elements
        
    def isEmpty(self):
        """ Méthode qui permet de savoir si le point à des éléments associé """
        return self.getElements() == []
    
    def removeElement(self, element):
        """ Méthode qui permet de retirer un élément de la list """
        if element in self.list_elements: self.list_elements.remove(element)
        
    def setChainage(self, new_chainage):
        """ Méthode qui permet de modifier le chainage du point de segmentation """
        self.chainage = new_chainage
    
    def setElements(self, elements):
        """ Méthode pour initialiser les éléments asocier au point """
        self.list_elements = []
        self.addElements(elements)
    
    def updateAttribut(self, name, new_val):
        """ Méthode qui permet de modifier un attributs du point de segmentation """
        if name in self.dict_attributs: self.dict_attributs[name] = new_val

class LinearReferencing:
    __slots__ = ("feat_rtss", "segmentation_points")
    
    # TODO: Faire des modifications afin que les chainages puissent être des nombres décimale
    def __init__(self, feat_rtss:featRTSS, list_segmentation_points=[]):
        # Objet de la class featRTSS
        self.feat_rtss = feat_rtss
        # Dictionnaire des segmentations sur le RTSS. La clé est la valeur du chainage et la 
        self.segmentation_points = {}
        # Ajouter les segmentations existantes
        self.addSegmentations(list_segmentation_points)
        
    def __repr__(self): return f"LinearReferencing {self.feat_rtss.getRTSS()}: {len(self.segmentation_points)} points de segmentation"
    
    def addElement(self, element, chainage_debut, chainage_fin, copy_elements=True):
        """
        Méthode qui permet d'ajouter un élément sur le RTSS
        
        Args:
            - element (any): Élement à ajouter
            - chainage_debut (reel/str): Chainage de début de l'élément
            - chainage_fin (reel/str): Chainage de fin de l'élément
            - copy_elements (bool): Conserver les éléments de la segmentation intersectée
        """
        chainage_debut = verifyFormatChainage(chainage_debut)
        chainage_fin = verifyFormatChainage(chainage_fin)
        # Ajouter un point de segmentation au chainage de début s'il y en a pas déjà une
        if not self.chainageExists(chainage_debut): self.addSegmentation(chainage_debut, copy_elements=copy_elements)
        # Ajouter un point de segmentation au chainage de fin s'il y en a pas déjà une
        if not self.chainageExists(chainage_fin): self.addSegmentation(chainage_fin, copy_elements=copy_elements)
        # Ajouter l'élément pour toutes les points de segmentations sur le RTSS
        for chainage in self.getListChainage(start=chainage_debut, end=chainage_fin)[:-1]: self.getSegmentation(chainage).addElement(element)
    
    def addSegmentation(self, segmentation_point, copy_elements=False):
        """
        Méthode qui permet d'ajouter un point de segmentation sur le RTSS
        
        Args:
            - segmentation_point (SegmentationPoint/real): Le point de segmentation ou chainage à ajouter
            - copy_elements (bool): Conserver les éléments de la segmentation intersectée
        """
        # Créer un point de segmentation si le point est seulement un chainage (nombre entier)
        if isinstance(segmentation_point, (int, float)): segmentation_point = SegmentationPoint(segmentation_point)
        # Vérifier que le chainage du point est sur le RTSS 
        if not self.feat_rtss.isChainageOnRTSS(segmentation_point.getChainage()):
            raise NameError(f"Le chainage {segmentation_point.getChainage()} n'est pas sur le RTSS {self.feat_rtss.getRTSS(formater=True)}")
        # Vérifier que le chainage est unique
        if self.chainageExists(segmentation_point.getChainage()):
            raise NameError(f"Le chainage {segmentation_point.getChainage()} est déjà sur le RTSS {self.feat_rtss.getRTSS(formater=True)}")
        
        # Ajouter la segmentation au RTSS
        self.segmentation_points[segmentation_point.getChainage()] = segmentation_point
        if copy_elements:
            # Définir la segmentation précédant 
            previous_segmentation = self.getPreviousSegmentation(segmentation_point)
            # Copier les éléements de la segmentation précédante
            if previous_segmentation: segmentation_point.setElements(previous_segmentation.getElements())
    
    def addSegmentations(self, list_segmentation_points):
        """
        Méthode qui permet d'ajouter plusieurs points de segmentation sur le RTSS
        
        Args:
            - list_segmentation_points (list): Liste de SegmentationPoint ou chainages à ajouter
        """
        for point in list_segmentation_points: self.addSegmentation(point)
    
    def chainageExists(self, chainage): 
        """ Méthode qui permet de vérifier si le chainage est unique dans le RTSS """
        return chainage in self.segmentation_points
    
    def getClosestSegmentation(self, chainage, dist_max=-1):
        """
        Méthode qui permet de retourner le point de segmentation le plus proche du chainage.
        
        Args:
            - chainage (str/real): Chainage à vérifier
            - dist_max (int): Distance maximun de la segmentation la plus proche
        """
        if self.isEmpty(): return None
        # Chainage le plus proche
        closest_chainage = min(self.getListChainage(), key=lambda x: abs(x - chainage))
        # Retourner rien si une distance max est défini et le point le plus proche est plus loin que la distance
        if abs(closest_chainage - chainage) > dist_max and dist_max != -1: return None
        return self.getSegmentation(closest_chainage)
    
    def getRTSS(self, formater=False):
        """ Méthode qui permet de retourner le numéro du RTSS """
        return self.feat_rtss.getRTSS(formater=formater)

    def getFeatRTSS(self):
        """ Méthode qui permet de retourner l'objet featRTSS """
        return self.feat_rtss
    
    def getListChainage(self, start=None, end=None):
        """
        Méthode qui permet de retourner une liste de toutes les chainages des segmentations entre un chainage de début et fin.
        Le début et la fin sont inclus.
        Args:
            - start (str/real): Le chainage de début de la recherche
            - end (str/real): Le chainage de fin de la recherche
        """
        # Retourner la liste de toutes les chainages des segmentations du RTSS si aucun début ou fin n'est défini
        if start is None and end is None: return sorted(list(self.segmentation_points.keys()))
        # Définir le chainage de début comme le début du RTSS s'il n'était pas défini
        if start is None: start = self.feat_rtss.getChainageDebut()
        # Définir le chainage de fin comme la fin du RTSS s'il n'était pas défini
        elif end is None: end = self.feat_rtss.getChainageFin()
        start, end = verifyFormatChainage(start), verifyFormatChainage(end)
        # Retourner toutes les chainages entres le début et la fin des chainage
        return sorted([chainage for chainage in self.segmentation_points.keys() if chainage >= start and chainage <= end])
    
    def getNextSegmentation(self, segmentation_point, check_end=False):
        """
        Méthode qui permet de retourner la prochaine segmentation sur le RTSS sois par un SegmentationPoint ou un chainage
        
        Args:
            - segmentation_point(real/str): La segmentation ou le chainage à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        segmentation_point = self.getSegmentation(segmentation_point)
        if segmentation_point is None: return segmentation_point
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
        
    def getNextChainage(self, segmentation_point, check_end=False):
        """
        Méthode qui permet de retourner le prochain chainage sur le RTSS sois par un SegmentationPoint ou un chainage
        
        Args:
            - segmentation_point(real/str): La segmentation ou le chainage à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        segmentation_point = self.getSegmentation(segmentation_point)
        next_segmentation = self.getNextSegmentation(segmentation_point, check_end=check_end)
        if next_segmentation != segmentation_point: return next_segmentation.getChainage()
        else: return None
    
    def getPreviousSegmentation(self, segmentation_point, check_end=False):
        """
        Méthode qui permet de retourner la segmentation précédant sur le RTSS sois par un SegmentationPoint ou un chainage
        
        Args:
            - segmentation_point(real/str): La segmentation ou le chainage à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        segmentation_point = self.getSegmentation(segmentation_point)
        if segmentation_point is None: return segmentation_point
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
    
    def getPreviousChainage(self, segmentation_point, check_end=False):
        """
        Méthode qui permet de retourner le chainage précédant sur le RTSS sois par un SegmentationPoint ou un chainage
        
        Args:
            - segmentation_point(real/str): La segmentation ou le chainage à analyser
            - check_end (bool): Considérer les points de segmentation vide
        """ 
        segmentation_point = self.getSegmentation(segmentation_point)
        previous_segmentation = self.getPreviousSegmentation(segmentation_point, check_end=check_end)
        if previous_segmentation != segmentation_point: return previous_segmentation.getChainage()
        else: return None
    
    def getSegmentation(self, value, exact=True):
        """
        Méthode qui permet de retourner un point de segmentation du RTSS sois par un SegmentationPoint ou un chainage
        
        Args:
            - value (str/real/SegmentationPoint): La valeur à rechercher
            - exact (bool): Retorurner seulement si la valeur est exactement une segmentation
        """
        # Retourner le point de segmentation exact seulement
        if exact:
            if isinstance(value, SegmentationPoint): 
                if value in self.segmentation_points.values(): return value
            else: return self.segmentation_points.get(value, None)
        # Retourner le point de segmentation d'un element
        elif isinstance(value, (int, float, str)):
            # Définir la listes des chainages sur le RTSS
            chainages = self.getListChainage()
            # Trouver l'index du point de segmentation au chainage avant ou égale 
            index = bisect.bisect_right(chainages, verifyFormatChainage(value))
            # Vérifier si l'index est valide
            if index > 0: 
                # Retourner le point de segmentation à l'index
                segmentation_point = self.segmentation_points.get(chainages[index - 1])
                if segmentation_point.isEmpty(): return None
                else: return segmentation_point
        return None
    
    def getSegmentationByAttribute(self, attribut, value):
        """ Méthode qui permet de retourner la liste des points de segmentation avec une valeur d'attribut """
        return [segmentation_point for segmentation_point in self.segmentation_points.values() if segmentation_point.getAttribut(attribut) == value] 
    
    def hasNextSegmentation(self, segmentation_point, check_end=True):
        """ Méthode qui permet de verifier si une segmentation à une segmentation suivant sur le RTSS """ 
        return segmentation_point != self.getNextSegmentation(segmentation_point, check_end=check_end)
     
    def hasPreviousSegmentation(self, segmentation_point, check_end=True):
        """ Méthode qui permet de verifier si une segmentation à une segmentation précédant sur le RTSS """
        return segmentation_point != self.getPreviousSegmentation(segmentation_point, check_end=check_end)
    
    def isEmpty(self):
        """ Méthode qui permet de vérifier si la segmentation du RTSS est vide """
        return self.segmentation_points == {}
    
    def moveSegmentation(self, segmentation_point, new_chainage):
        """ 
        Méthode qui permet de déplacer une segmentation à un chainage différent
        
        Args:
            - segmentation_point(str/real/SegmentationPoint): Le point de segmentation à déplacer
            - new_chainage(real/str): Le nouveau chainage de la segmentation
        """
        segmentation_point = self.getSegmentation(segmentation_point)
        if segmentation_point is None: return False
        new_chainage = verifyFormatChainage(new_chainage)
        # Vérifier que le nouveau chainage n'existe pas et qu'il est sur le RTSS 
        if self.chainageExists(new_chainage) or not self.feat_rtss.isChainageOnRTSS(new_chainage): return False
        new_segmentation_point = segmentation_point.copy()
        # Modifier le chainage de la segmentation pour le nouveau chainage
        new_segmentation_point.setChainage(new_chainage)
        # Retirer la segmentation
        self.removeSegmentation(segmentation_point.getChainage())
        # Ajouter la nouvelle segmentation
        self.addSegmentation(new_segmentation_point)
        return True
    
    def removeSegmentation (self, segmentation_point, check_end=False):
        """
        Méthode qui permet de supprimer une segmentation du RTSS
        
        Args:
            - segmentation_point(str/real/SegmentationPoint): Le point de segmentation à supprimer
            - check_end (bool): Considérer les points de segmentation vide
        """
        segmentation_point = self.getSegmentation(segmentation_point)
        if segmentation_point is None: return False
        if (self.hasPreviousSegmentation(segmentation_point) and
            check_end and segmentation_point.isEmpty() and
            not self.hasNextSegmentation(segmentation_point, check_end=False)): return False
        
        return self.segmentation_points.pop(segmentation_point.getChainage(), False) is not False
        
class ReseauSegmenter:
    """ Méthode qui permet de gérer un groupe de RTSS segmentés. """

    def __init__(self, geocode=None):
        """
        Constructeur de l'objet ReseauSegmenter

        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau 
        """
        self.reseau = {}
        self.setModuleGeocodage(geocode)
    
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
        reseau_segmenter = cls(geocode)
        # Parourir toutes les entitées de la couche
        for feat in layer.getFeatures(filter_request):
            # Definir l'objet LinearReferencing
            rtss_segmenter = reseau_segmenter.getRTSSSegmenter(feat[champ_rtss])
            # Vérifier si l'objet LinearReferencing est valide
            if rtss_segmenter is None: continue
            # Définir le chainage de début de l'entitée
            cd = rtss_segmenter.getFeatRTSS().getChainageOnRTSS(feat[champ_cd])
            # Définir le chainage de fin de l'entitée
            cf = rtss_segmenter.getFeatRTSS().getChainageOnRTSS(feat[champ_cf])
            # Ajouter l'id du projet au module de référence linéraire du RTSS
            rtss_segmenter.addElement(feat.id(), cd, cf)
        return reseau_segmenter

    @classmethod
    def fromLayerInterpolation(cls, geocode, layer, field_value, fields_route=[], step=10, max_dist=20):
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
        reseau_segmenter = cls(geocode)
        # Localisation des vitesses
        index_vitesse = QgsSpatialIndex(layer.getFeatures(), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        # Pourcourir toutes les modules de référence linéraire des RTSS
        for rtss_segmenter in reseau_segmenter.reseau.values():
            # Définir le featRTSS du référence linéraire courant
            feat_rtss = rtss_segmenter.getFeatRTSS()
            numero_route = feat_rtss.getRTSS()[:5]
            # Parcourir les chainages des RTSS
            for c in range(int(feat_rtss.getChainageDebut()), int(feat_rtss.getChainageFin()), step):
                # Géometrie du point de chainage
                point_geom = feat_rtss.getPointFromChainage(c)
                # Valeurs d'ID et de distance par défault
                feat_id, min_dist = None, max_dist+1
                # Parcourir les ID des entitées à proximité
                for id in index_vitesse.nearestNeighbor(point_geom.asPoint(), 5, maxDistance=max_dist):
                    # Vérifier que les numéros de routes sont les mêmes si un champs est spécifié
                    if fields_route == []: pass
                    elif not any([layer.getFeature(id)[f][:5] == numero_route for f in fields_route]): continue
                    # Calculer la vrai distances entre les deux geometry
                    distance = layer.getFeature(id).geometry().distance(point_geom)
                    # Conserver la distances la plus petite 
                    if distance < min_dist: feat_id, min_dist = id, distance
                
                # Définir la valeur 
                if feat_id is None: value = None
                else: value = layer.getFeature(feat_id)[field_value]
                # Vérifier si la valeur de la segmentation au chainage courant est la même que la valeur la plus proche
                try: 
                    if value in rtss_segmenter.getSegmentation(c, exact=False).getElements(): continue
                except: pass
                # Sinon ajouter une segmentation avec la valeur la plus proche au chainage courant
                rtss_segmenter.addElement(value, c, feat_rtss.getChainageFin(), copy_elements=False)
        return reseau_segmenter

    def setModuleGeocodage(self, geocode:geocodage):
        """
        Méthode qui permet de définir le module de geocodage sur lequel baser le réseau.

        Args:
            - geocode (geocodage): L'objet geocodage sur lequel baser le réseau
        """
        self.geocode = geocode
        print(self.geocode)
        self.reseau = {feat_rtss.getRTSS(): LinearReferencing(feat_rtss) for feat_rtss in self.geocode.getListFeatRTSS()}
 
    def addRTSSSegmenter(self, rtss_segmenter, overide=False):
        """
        Méthode qui permet d'ajouter un RTSS segmenté au réseau.

        Args:
            - rtss_segmenter (LineairReferencing): L'objet qui contient les segmentations sur le RTSS 
            - overide (bool): Effacer le RTSS existant
        """
        if overide or not rtss_segmenter.getRTSS() in self.reseau:
            self.reseau[rtss_segmenter.getRTSS()] = rtss_segmenter

    def getRTSSSegmenter(self, rtss):
        """
        Méthode qui permet de retourner le RTSS segmenter

        Args:
            - rtss (str): Le numéro du RTSS 
        """
        return self.reseau.get(verifyFormatRTSS(rtss), None)
    
    def getElementsFromChainage(self, rtss, chainage):
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par un rtss et chainage.

        Args:
            - rtss (str): Le numéro de rtss de la localisation
            - chainage (str/real): La valeur du chainage de la localisation
        """
        rtss_segmenter = self.getRTSSSegmenter(rtss)
        if rtss_segmenter is None: return None
        return rtss_segmenter.getSegmentation(chainage, exact=False).getElements()
    
    def getElementsFromPoint(self, point):
        """
        Méthode qui permet de retourner la valeur des éléments d'un PointSegmentation a un
        point donnée sur le réseau. Le point est défini par une localisation ponctuelle.

        Args:
            - point (QgsGeometry/QgsPointXY): La localisation du point
        """
        result = self.geocode.getPointOnRTSS(point)
        return self.getElementsFromChainage(result[1], result[2])
        


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        