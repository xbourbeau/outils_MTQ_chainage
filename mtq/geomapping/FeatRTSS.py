# -*- coding: utf-8 -*-
# Importer les objects du module core de QGIS 
from qgis.core import QgsGeometry, QgsPointXY, QgsGeometryUtils, QgsPoint, QgsFeature

# Importer les fonction de formatage du module
from ..functions.interpolateOffsetOnLine import interpolateOffsetOnLine
from ..functions.offsetPoint import offsetPoint

# Importer la librairie pour des opérations trigo
import math
import copy
from typing import Union

# Librairie MTQ
from .RTSS import RTSS
from .Chainage import Chainage
from .LineRTSS import LineRTSS
from .PointRTSS import PointRTSS
from .PolygonRTSS import PolygonRTSS

from ..param import (DEFAULT_NOM_CHAMP_RTSS, DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                     DEFAULT_NOM_CHAMP_FIN_CHAINAGE)

class FeatRTSS(RTSS):
    """
    Class qui défini un objet FeatRTSS.
    Elle permet ainsi de regrouper les méthodes pouvant être associer au RTSS (géocodage)
    """
    __slots__ = ("num_rts", "chainage_d", "chainage_f", "attributs", "geom", "geom_densify", "use_densify_geom")

    def __init__ (self, num_rtss, chainage_f, geometry:QgsGeometry, chainage_d=0, **kwargs):
        """
        Méthode d'initialitation de la class. Le RTSS et chainage de fin peuvent être formater, mais sont stockée
        non formater. Le chainage de début est assumé comme étant 0
        
        Args:
            - num_rtss (str): Le numéro de RTSS
            - chainage_f (real/str): Le chainage de fin du RTSS, sois sa longueur en chainage
            - geometry (QgsGeometry): La geometrie du RTSS
            - chainage_d (real/str): Le chainage de début du RTSS, par défault toujours 0
            - kwargs: Attributs suplémentaire du RTSS
        """
        # Initialiser les informations du RTSS
        self.setChainageDebut(chainage_d)
        self.setChainageFin(chainage_f)
        self.geom = geometry
        self.geom_densify = self.geom.densifyByDistance(5)
        self.use_densify_geom = False

        RTSS.__init__(self, num_rtss, **kwargs)
        
    @classmethod
    def fromFeature(cls, feat:QgsFeature,
                    nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS,
                    nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE,
                    chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE,
                    **kwargs):
        """
        Méthode d'initialitation de la class à partir d'une entitée.

        Args:
            - feat (QgsFeature): L'entitié du RTSS
            - nom_champ_rtss (str): Le nom du champ contenant le RTSS
            - nom_champ_long (str): Le nom du champ contenant le chainage de fin
            - chainage_d (str): Le nom du champ contenant le chainage de début
            - kwargs: Attributs suplémentaire du RTSS (nom de l'attribut = nom du champs de la valeur)
        """
        if isinstance(feat, QgsFeature):
            # Définir le chainage de début
            chainage_d = 0 if chainage_d is None else feat[chainage_d]
            rtss = cls(feat[nom_champ_rtss], feat[nom_champ_long], feat.geometry(), chainage_d=chainage_d)
            for name, val in kwargs.items(): 
                if val: rtss.setAttribut(name, feat[val])
            return rtss
        else: return cls(None, None, None)
    
    def __str__ (self): return f"{self.num_rts} ({self.chainage_d}, {self.chainage_f})"
    
    def __repr__ (self): return f"FeatRTSS {self.num_rts} ({self.chainage_d}, {self.chainage_f})"
    
    def __contains__(self, key): return self.chainage_d <= key and self.chainage_f >= key

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

    def asLineRTSS(self, offset=0):
        """
        Permet de retourner un objet LineRTSS représantant le RTSS
        
        Args:
            - offset (float): Un offset du RTSS. Défault = 0
        """
        return self.createLine([self.chainageDebut(), self.chainageFin()], offsets=[offset])

    def chainageDebut(self) -> Chainage:
        """ Renvoie le chainage de début du RTSS """
        return self.chainage_d

    def chainageFin(self) -> Chainage:
        """ Renvoie le chainage de fin du RTSS, sois sa longueur en chainage. """
        return self.chainage_f

    def createLine(self, chainages:list[int, float, Chainage, str], offsets:list=[0], interpolate_on_rtss=True) -> LineRTSS:
        """
        Méthode qui permet de créer un LineRTSS sur le RTSS
        
        Args:
            - chainages (list): La liste des chainages pour créer la ligne
            - offsets (list): Liste des offsets des points de la ligne
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points

        Return (LineRTSS): La LineRTSS créer
        """
        list_point_rtss = []
        nbr_offset = len(offsets)
        for i, chainage in enumerate(chainages):
            if i+1 > nbr_offset: i = nbr_offset-1
            list_point_rtss.append(self.createPoint(chainage, offsets[i]))
        # Créer la ligne sur le RTSS
        return LineRTSS(list_point_rtss, interpolate_on_rtss=interpolate_on_rtss)

    def createPoint(self, chainage:Union[int, float, Chainage, str], offset=0) -> PointRTSS:
        """ Méthode qui permet de créer un PointRTSS sur le RTSS """
        return PointRTSS(self.getRTSS(), self.getChainageOnRTSS(chainage), offset)

    def createPolygon(self, chainages:list[int, float, Chainage, str], offsets:list, interpolate_on_rtss=True) -> PolygonRTSS:
        """
        Méthode qui permet de créer un PolygonRTSS sur le RTSS
        
        Args:
            - chainages (list): La liste des chainages pour créer le polygon
            - offsets (list): Liste des offsets des points du polygon
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points

        Return (PolygonRTSS): Le PolygonRTSS créer
        """
        # Vérifier que le nombre de chainages et de offsets sont identique
        if len(chainages) != len(offsets): raise ValueError("Le nombre de chainages et de offsets doivent etre identique")
        # Créer la liste des points pour le polygon
        list_point_rtss = [self.createPoint(chainage, offsets[i]) for i, chainage in enumerate(chainages)]
        # Créer le polygon sur le RTSS
        return PolygonRTSS(list_point_rtss, interpolate_on_rtss=interpolate_on_rtss)
    
    def createPolygonFromSize(self, chainage:Chainage, width, height, offset=0, interpolate_on_rtss=True) -> PolygonRTSS:
        """
        Méthode qui permet de créer un PolygonRTSS sur le RTSS à partir d'un point de référence (chainage/offset)
        et des valeurs de longueur et hauteur.
        La longueur est calculer parralelement au RTSS et la hauteur perpendiculairement.
        
        Args:
            - chainage (Chainage): Le chainage du début du polygon
            - width (int/float): La longueur du polygon parralelement au RTSS 
            - height (int/float): la hauteur du polygon perpendiculairement au RTSS 
            - offset (int/float): Le offset du polygon par rapport à la trace
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points

        Return (PolygonRTSS): Le PolygonRTSS créer
        """
        chainages = [chainage, Chainage(chainage)+width, Chainage(chainage)+width, chainage]
        offsets = [offset, offset, offset+height, offset+height]
        # Créer le polygon sur le RTSS
        return self.createPolygon(chainages, offsets, interpolate_on_rtss=interpolate_on_rtss)

    def geocoder(self, obj_rtss:Union[PointRTSS, LineRTSS, PolygonRTSS], on_rtss=False, interpolate_on_rtss=None):
        """
        Permet de géocoder un objet de localition RTSS (PointRTSS, LineRTSS ou PolygonRTSS)
        sur le RTSS
        
        Args:
            - obj_rtss (PointRTSS, LineRTSS, PolygonRTSS): L'objet à géocoder sur le RTSS
            - on_rtss(bool): Permet d'overide la valeur de offset en géocodant l'objet_rtss sur le RTSS
            - interpolate_on_rtss(bool): Permet d'overide l'interpolation de l'objet_rtss sur le RTSS 
        
        Return (QgsGeometry): La géometry géocoder sur le RTSS
        """
        if isinstance(obj_rtss, PointRTSS): return self.geocoderPoint(obj_rtss, on_rtss=on_rtss)
        elif isinstance(obj_rtss, LineRTSS): return self.geocoderLine(obj_rtss, on_rtss=on_rtss, interpolate_on_rtss=interpolate_on_rtss)
        elif isinstance(obj_rtss, PolygonRTSS): return self.geocoderPolygon(obj_rtss, on_rtss=on_rtss, interpolate_on_rtss=interpolate_on_rtss)

    def geocoderInverse(self, geometry:QgsGeometry):
        """
        Permet de faire le géocodage inverse donc de convertir une géometry en objet 
        de localition RTSS (PointRTSS, LineRTSS ou PolygonRTSS) sur le RTSS.
        
        Args:
            - geometry (QgsGeometry): La géometry à utiliser pour créer l'objet sur le RTSS
        
        Return (PointRTSS, LineRTSS, PolygonRTSS): L'objet RTSS
        """
        geometry.convertToSingleType()
        if geometry.wkbType() == 1: return self.geocoderInversePoint(geometry)
        elif geometry.wkbType() == 2: return self.geocoderInverseLine(geometry)
        elif geometry.wkbType() == 3: return self.geocoderInversePolygon(geometry)

    def geocoderInverseLine(self, geometry:QgsGeometry):
        """
        Permet de convertir une géometry linéaire en objet LineRTSS
        
        Args:
            - geometry (QgsGeometry): La géometry à utiliser pour créer l'objet LineRTSS
        
        Return (LineRTSS): L'objet LineRTSS équivalent a la géometry
        """
        geometry.convertToSingleType()
        list_geom_point = geometry.asPolyline()
        # Géocodage inverse de l'extremitées
        point_d = self.geocoderInversePoint(QgsGeometry.fromPointXY(list_geom_point[0]))
        point_f = self.geocoderInversePoint(QgsGeometry.fromPointXY(list_geom_point[-1]))
        
        # TODO: Défine interpolate_on_rtss with a random point on the ligne
        #interpolate_on_rtss = self.getDistanceFromPoint(list_geom_point[int(len(list_geom_point)/2)])
        
        return LineRTSS([point_d, point_f])

    def geocoderInversePoint(self, geometry:Union[QgsGeometry, QgsPoint, QgsPointXY]):
        """
        Permet de convertir une géometry ponctuel en objet PointRTSS
        
        Args:
            - geometry (QgsGeometry/QgsPoint/QgsPointXY): La géometry ponctuel à utiliser pour créer l'objet PointRTSS
        
        Return (PointRTSS): L'objet PointRTSS équivalent a la géometry
        """
        geometry = FeatRTSS.verifyFormatPoint(geometry)
        geometry.convertToSingleType()
        # Définir le offset du point
        offset = self.getDistanceFromPoint(geometry)
        # Trouver le chainage du point sur le RTSS
        chainage = self.getChainageFromPoint(geometry)
        # Retourner une liste des informations trouvé
        return self.createPoint(chainage, offset)

    def geocoderInversePolygon(self, geometry:QgsGeometry):
        """
        Permet de convertir une géometry polygonal en objet PolygonRTSS
        
        Args:
            - geometry (QgsGeometry): La géometry à utiliser pour créer l'objet PolygonRTSS
        
        Return (PolygonRTSS): L'objet PolygonRTSS équivalent a la géometry
        """
        # TODO: Défine interpolate_on_rtss with a random point
        list_point_rtss = []
        for point in geometry.vertices():
            # Géocodage inverse de l'extremitées
            list_point_rtss.append(self.geocoderInversePoint(QgsGeometry.fromPointXY(QgsPointXY(point))))
            # TODO: Remove unecessary points 
        return PolygonRTSS(list_point_rtss)

    def geocoderLine(self, line:LineRTSS, on_rtss=False, interpolate_on_rtss=None):
        """
        Méthode qui permet de géocoder une ligne sur un RTSS à partir d'un objet LineRTSS.
        La ligne peux être géocoder en interpolant la trace du RTSS entres les points de la ligne ou
        seulement géocoder les points de la ligne.
        
        Args:
            - line (LineRTSS): La ligne à géocoder
            - on_rtss(bool): Permet d'overide la valeur de offset en géocodant le point sur le RTSS 
            - interpolate_on_rtss(bool): Permet d'overide l'interpolation de l'objet LineRTSS sur le RTSS 
        
        Return (QgsGeometry): La géometrie linéaire géocoder
        """
        # Vérifier que la ligne contient un seule RTSS
        if not self.isLineOnRTSS(line): 
            raise Exception("La ligne doit etre entierement sur le RTSS")
        # Indentifier si la ligne doit être interpoler sur le RTSS entre les 2 PointRTSS de la ligne
        if interpolate_on_rtss is None: interpolate_on_rtss = line.interpolate()
        # Géocoder le premier point de la ligne
        start_point_geom = self.geocoderPoint(line.startPoint(), on_rtss=on_rtss)
        line.startPoint().setGeometry(start_point_geom)
        # Liste des points de la ligne géocodée
        line_points = [start_point_geom.asPoint()]
        # Parcourir les points de la ligne à partir du deuxième point
        for idx, line_point in enumerate(line.getPoints()[1:]):
            point_geom = self.geocoderPoint(line_point, on_rtss=on_rtss)
            # Géocoder le point de la ligne 
            line[idx+1].setGeometry(point_geom)
            # Vérifier si la ligne doit être interpoler sur le RTSS entre les 2 PointRTSS de la ligne
            if interpolate_on_rtss:
                # Ajouter les points des vertex entre les deux dernier PointRTSS de la ligne
                line_points.extend(self.geocoderLineFromExtremities(line[idx], line[idx+1], on_rtss=on_rtss))
            # Ajouter le dernier points à la liste
            line_points.append(point_geom.asPoint())
        
        # Créer la géometrie de la ligne à partir de la liste des vertex
        line_geom = QgsGeometry().fromPolylineXY(line_points)
        # Retirer des vertex qui serait doublé
        line_geom.removeDuplicateNodes()
        line_geom = line_geom.simplify(0.01)
        # Retourner la géometrie de la ligne
        return line_geom
    
    def getVertexBetweenPoints(self, start_point:QgsGeometry, end_point:QgsGeometry, is_reverse=False):
        # Définir l'incrémentation du range pour parcourir les vertex
        increment = -1 if is_reverse else 1
        # Définir le vertex le plus proche du premier point 
        start_vertex = self.geometry().closestVertex(start_point.asPoint())[1]
        # Définir le vertex le plus proche du dernier point
        end_vertex = self.geometry().closestVertex(end_point.asPoint())[1]
        # Liste des distances le long de la ligne pour les deux points
        dists = [self.geometry().lineLocatePoint(start_point), self.geometry().lineLocatePoint(end_point)]
        # Définir les distances Min/Max
        dist_min, dist_max = min(dists), max(dists)
        # Liste des vertex entre les points
        list_vertex_idx = []
        # Parcourir les vertex entre les points vertex le plus proche des points
        for vertex_idx in range(start_vertex, end_vertex+increment, increment):
            # Vérifier que le vertex est bien entre les points avec la distance 
            if vertex_idx == start_vertex or vertex_idx == end_vertex:
                dist_vertex = self.geometry().lineLocatePoint(QgsGeometry.fromPoint(self.geometry().vertexAt(vertex_idx)))
                if dist_vertex <= dist_min or dist_vertex >= dist_max: continue
            # Ajouter le vertex à la liste
            list_vertex_idx.append(vertex_idx)
        # Retourner la liste des vertexs
        return list_vertex_idx

    def geocoderLineFromExtremities(self, start_point:PointRTSS, end_point:PointRTSS, on_rtss=False):
        # Vérifier que le début et la fin sont sur un seule RTSS
        if start_point.getRTSS() != end_point.getRTSS():
            raise Exception("La ligne doit etre entierement sur le RTSS")
        # Liste des points de la ligne géocodée
        line_points = []
        # Longueur entre les deux points de la ligne
        length = abs(float(start_point.getChainage() - end_point.getChainage()))
        # Indicateur que la section de ligne est dans le sense inverse du chainage
        is_reverse = start_point.getChainage() > end_point.getChainage()
        # Vérifier si le offset des vertex devrait être interpoler
        interpolate_offset = not on_rtss and start_point.getOffset() != end_point.getOffset()
        # Définir le chainage avec le premier point si le offset est le même
        if not interpolate_offset: offset = start_point.getOffset()
        # Définir le offset à 0 si c'est sur le RTSS
        if on_rtss: offset = 0

        if interpolate_offset: self.use_densify_geom = True
        elif offset != 0: self.use_densify_geom = True

        # Le suivi de la mesure de la distance de la ligne le long du RTSS
        dist_along_line = 0
        # Définir le premier vertex comme étant le point de début sur le RTSS
        previous_vertex = self.geocoderPointFromChainage(start_point.getChainage()).asPoint()
        # Définir la géometrie du point de départ sur le RTSS
        start_point_geom_on_line = self.geocoderPoint(start_point, on_rtss=True) if start_point.getOffset() != 0 else start_point.getGeometry()
        # Définir la géometrie du point de fin sur le RTSS
        end_point_geom_on_line = self.geocoderPoint(end_point, on_rtss=True) if end_point.getOffset() != 0 else end_point.getGeometry()
        # Parcourir les vertex entre le dernier point et le point courant
        for vertex_idx in self.getVertexBetweenPoints(start_point_geom_on_line, end_point_geom_on_line, is_reverse):
            # Définir la coordonnée du vertex courant
            vertex_point = QgsPointXY(self.geometry().vertexAt(vertex_idx))
            # Vérifier si la ligne à un offset de défini
            if interpolate_offset:
                # Incrémenter la distance de la ligne le long du RTSS
                dist_along_line += float(self.getChainageFromLong(vertex_point.distance(previous_vertex)))
                # Conserver le vertex comme étant le dernier point utilisé
                previous_vertex = vertex_point
                # Définir le offset au vertex courant
                offset = interpolateOffsetOnLine(
                    dist=dist_along_line,
                    longeur=length,
                    offset_d=start_point.getOffset(),
                    offset_f=end_point.getOffset())
            # Appliquer un offset au point du vertex
            if offset != 0:
                vertex_point = offsetPoint(
                    point=vertex_point,
                    offset=offset,
                    angle=self.geometry().angleAtVertex(vertex_idx))
            
            # BUG: Fix pour des offset différent
            vals = self.geometry().closestSegmentWithContext(vertex_point)
            dist = vals[1].distance(vertex_point)
            # Ajouter le vertex à la ligne géocoder
            if dist+0.01 >= abs(offset): line_points.append(vertex_point)

        self.use_densify_geom = False
        # Retourner la liste des points de la ligne
        return line_points

    def geocoderLineFromChainage(self, chainages:list[Chainage], offsets:list=[0], interpolate_on_rtss=True):
        """
        Méthode qui permet de géocoder une ligne sur un RTSS à partir d'une list de chainage.
        Un offset de début et de fin peuvent aussi être définie.
        La ligne peux être géocoder en interpolant la trace du RTSS entres les points de la ligne ou
        seulement géocoder les points de la ligne.
        
        Args:
            - chainages (list): La liste des chainages pour créer la ligne
            - offsets (list): Liste des offsets des points de la ligne (1 offset == parralel)
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points
        
        Return (QgsGeometry): La géometrie linéaire géocoder
        """
        line_rtss = self.createLine(chainages, offsets=offsets, interpolate_on_rtss=interpolate_on_rtss)
        return self.geocoderLine(line_rtss)

    def geocoderPoint(self, point:PointRTSS, on_rtss=False):
        """
        Méthode qui permet de géocoder un PointRTSS sur le RTSS.
        
        Args:
            - point (PointRTSS): Le point à géocoder
            - on_rtss(bool): Permet d'overide la valeur de offset en géocodant sur le RTSS
        
        Return (QgsGeometry): La geometry du point géocodé sur le RTSS 
        """
        if not isinstance(point, PointRTSS): 
            raise ValueError("Un objet PointRTSS doit etre utiliser")
        # Longeur géometrique le long du RTSS correspondant au chainage
        long = self.getLongFromChainage(point.getChainage())
        # Geometry du point à la distance
        geom_point = self.geometry().interpolate(long)
        # Calculer le point avec la distance d'offset
        if point.hasOffset():
            geom_point = QgsGeometry().fromPointXY(offsetPoint(
                point=geom_point.asPoint(),
                offset=0 if on_rtss else point.getOffset(),
                # Angle en radian du RTSS au chainage dans le sense horraire par raport au Nord
                angle=self.geometry().interpolateAngle(long)))
        # Retourner la géometrie ponctuelle
        return geom_point

    def geocoderPointFromChainage(self, chainage:Union[int, float, Chainage, str], offset=0):
        """
        Méthode qui permet de géocoder un point avec un chainage et un offset sur le RTSS.
        Le offset de la ligne par rapport au RTSS peut être positif pour un offset à droite dans le sense
        de numérisation de la ligne ou négatif pour être à gauche.
        
        Args:
            - chainage (real/str): Le chainage du point à géocoder. Peut être formater ex: (2+252 ou 2252)
            - offset (real): Le offset du point par rapport au RTSS (positif = droite / négatif = gauche)
        
        Return (QgsGeometry): La geometry du point géocodé sur le RTSS 
        """
        return self.geocoderPoint(self.createPoint(chainage, offset))
    
    def geocoderPolygon(self, polygon:PolygonRTSS, interpolate_on_rtss=None):
        """
        Méthode qui permet de géocoder un polygon sur un RTSS à partir d'un objet PolygonRTSS.
        Le polygon peux être géocoder en interpolant la trace du RTSS entres les points ou
        seulement géocoder les points du polygon.
        
        Args:
            - line (PolygonRTSS): Le polygon à géocoder
            - interpolate_on_rtss(bool): Permet d'overide l'interpolation de l'objet PolygonRTSS sur le RTSS 
        
        Return (QgsGeometry): La géometrie polygonal géocoder
        """
        # Vérifier que le polygon est valide
        if not polygon.isValide(): raise ValueError(f"{polygon} is not valide. It needs at least 4 points and should be closed")
        # Indentifier si la ligne doit être interpoler sur le RTSS entre les 2 PointRTSS de la ligne
        if interpolate_on_rtss is None: interpolate_on_rtss = polygon.interpolate()
        # Définir une liste de points géocoder du polygon
        list_polygon_points = []
        # Nombre de points que contient le polygon
        point_count = polygon.pointCount() - 1
        # Parcourir les points du polygon
        for idx, point in enumerate(polygon.getPoints()):
            # Géocoder seulement le point
            if idx == point_count or not polygon.interpolate(): 
                list_polygon_points.append(self.geocoderPoint(point).asPoint())
            # Geocoder la ligne pour avoir les points entre les deux points du polygon
            else: list_polygon_points.extend(
                self.geocoderLine(
                    LineRTSS([point, polygon[idx+1]], interpolate_on_rtss=interpolate_on_rtss),
                    ).asPolyline()[:-1])
        # Retourn la géometrie polygonal (Si moins de 3 point la géometrie est NULL)
        return QgsGeometry().fromPolygonXY([list_polygon_points]).makeValid()

    def geocoderPolygonFromChainage(self, chainages:list[int, float, Chainage, str], offsets, interpolate_on_rtss=True):
        """
        Méthode qui permet de géocoder un polygon sur un RTSS à partir d'une liste de chainage et de offset.
        Le polygon peux être géocoder en interpolant la trace du RTSS entres les points ou
        seulement géocoder les points du polygon.
        
        Args:
            - chainages (list): La liste des chainages pour créer le polygon
            - offsets (list): Liste des offsets des points du polygon
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points

        Return (QgsGeometry): La géometrie polygonal géocoder
        """
        # Créer le polygon
        polygon = self.createPolygon(chainages, offsets, interpolate_on_rtss=interpolate_on_rtss)
        # Retourner le polygon géocoder
        return self.geocoderPolygon(polygon)

    def geometry(self)->QgsGeometry:
        """ Méthode qui renvoie la géometrie du RTSS """
        if self.use_densify_geom: return self.geom_densify
        return self.geom
 
    def densifyGeometry(self)->QgsGeometry:
        """ Méthode qui renvoie la géometrie du RTSS densifié """
        return self.geom_densify

    def getChainageOnRTSS(self, chainage:Union[int, float, Chainage, str]):
        """ 
        Méthode qui renvoie le chainage en entrée sur RTSS. 
        Elle s'asure que le chainage ne sois pas plus petit ou plus grand que les chainages du RTSS
        """
        chainage = Chainage(chainage)
        # Retourner le chainage de début si le chainage en entrée est plus petit
        if chainage < self.chainage_d: return self.chainage_d
        # Retourner le chainage de fin si le chainage en entrée est plus grand
        elif chainage > self.chainage_f: return self.chainage_f
        # Sinon retourner le chainage en entrée
        else: return chainage
    
    def getDistanceFromPoint(self, point:Union[QgsPointXY, QgsGeometry])->float:
        """
        Méthode qui permet de calculer une distance trace d'un point par rapport au RTSS.
        La distance du point par rapport au RTSS (positif = droite / négatif = gauche)
        
        Args:
            - point (QgsGeometry/QgsPointXY): Le point à trouver la distance du RTSS
        
        Return (float): La distance du point par rapport au RTSS (positif = droite / négatif = gauche)
        """
        point_geom = FeatRTSS.verifyFormatPoint(point)
        # Retourner la distance et appliquer le coté (1=droit ; -1=gauche)
        return self.geometry().distance(point_geom) * self.side(point_geom)
        
    def getChainageFromPoint(self, point:Union[QgsPointXY, QgsGeometry]):
        """ 
        Méthode qui permet d'associer un chainage le long du RTSS à partir d'un point. Le point peut être sur la 
        la ligne ou avoir un offset. 
        
        Args:
            - point (QgsGeometry/QgsPointXY): Le point à associer un chainage
        
        Return (real/str): Le chainage sur le RTSS le plus proche du point. 
        """
        # Longueur le long de la ligne jusqu'au point le plus proche du point spécifié
        long = self.geometry().lineLocatePoint(FeatRTSS.verifyFormatPoint(point))
        # Chainage corriger correspondant à la longueur trouvé
        return self.getChainageFromLong(long)
    
    def getLongFromChainage(self, chainage:Union[int, float, Chainage, str])->float:
        """ 
        Méthode qui retourne le chainage correspondant à la longueur demandé le long du RTSS
        Chaînage --> Distance géometrique
        
        Args:
            - chainage (float/int): Le chainage à convertir en longueur géometrique 
        
        Return (float/int): La longueur géometrique correspondant au chainage en entrée
        """
        # L'objet Chainage 
        chainage = Chainage(chainage)
        # Retourner la longueur geometrique max si le chainage est plus grande que le chainage de fin 
        if chainage >= self.chainage_f: return self.length()
        # Retourner le chainage de début du RTSS si le chainage est plus petit que le chainage de début du RTSS
        elif chainage <= self.chainage_d: return float(self.chainage_d)
        # Sinon corriger le chainage pour obtenir la longueur géometrique
        else: return float((chainage * self.length()) / self.chainage_f.value())
    
    def getChainageFromLong(self, longueur:Union[int, float]):
        """ 
        Méthode qui retourne le chainage correspondant à la longueur demandé le long du RTSS
        Distance géometrique --> Chaînage
        
        Args:
            - longueur (float/int): La longueur géometrique à corriger le long du RTSS
        
        Return (Chainage): Le chainage correspondant à la longueur en entrée
        """
        # Longueur du RTSS
        long_rtss = self.geometry().length()
        # Retourner le chainage de fin si la longueur est plus grande que la longueur du RTSS
        if longueur >= long_rtss: return self.chainage_f
        # Si la longueur est plus petit que le chainage de début du RTSS retourner le chainage de début du RTSS
        elif self.chainage_d >= longueur: return self.chainage_d 
        else: return Chainage((self.chainage_f * longueur)/ long_rtss)

    def getRTSS(self):
        """ Permet de retourner l'ojet RTSS de la class """
        rtss = RTSS(self.value())
        rtss.attributs = self.attributs
        return rtss

    def getTransect(self, chainage:Union[int, float, Chainage, str], dist_d, dist_g, inverse=False):
        """
        Méthode qui crée une ligne perpendiculaire au RTSS.
        Par défault le transect est de gauche => droite, mais peut être inversé droite => gauche.

        Args:
            - chainage (real/str): Chainage du transect. Peut être formater ex: (2+252 ou 2252)
            - dist_d (real): Longueur du transect à droite.
            - dist_g (real): Longueur du transect à gauche.
            - inverse (bool): Sense du transect True:[droite => gauche] False:[gauche => droite]
        
        Return (QgsGeometry): La géometrie linéaire du transect
        """
        # Point à droite du RTSS
        pt_droit = self.geocoderPointFromChainage(chainage, offset=dist_d)
        # Point à gauche du RTSS
        pt_gauche = self.geocoderPointFromChainage(chainage, offset=dist_g*-1)
        # Inverser les points si spécifié
        if inverse: pt_droit, pt_gauche = pt_gauche, pt_droit
        # Retourner la ligne entre les deux points
        return QgsGeometry().fromPolylineXY([pt_gauche.asPoint(), pt_droit.asPoint()])
    
    def getAngleAtChainage(self, chainage:Union[int, float, Chainage, str]):
        """
        Méthode qui permet de retourner l'angle le long de la ligne à un chainage.

        Args:
            - chainage (str/real): Le chainage pour lequel mesurer l'angle

        Return (float): l'angle en degrees au chainage
        """
        # Longueur géometrique correspondant au chainage
        long = self.getLongFromChainage(chainage)
        # Angle en radian du RTSS au chainage dans le sense horraire par raport au Nord
        angle = self.geometry().interpolateAngle(long)
        # Retourner l'angle en degrees
        return math.degrees(angle)
    
    def interpolateOffsetAtChainage(self, chainage, chainage_d, chainage_f, offset_d, offset_f):
        """
        Méthode qui permet de calculer le offset d'une ligne à un chainage par rapport au RTSS.

        Args:
            - chainage (str/real): Le chainage pour lequel interpoler le offset
            - chainage_d (str/real): Le chainage de début de la ligne
            - chainage_f (str/real): Le chainage de fin de la ligne
            - offset_d (real): Le offset de début de la ligne
            - offset_f (real): Le offset de fin de la ligne
        """
        if chainage_d == chainage_f: return None
        if offset_d == offset_f: return offset_d
        long_d = self.getLongFromChainage(chainage_d)
        long_f = self.getLongFromChainage(chainage_f)
        long = self.getLongFromChainage(chainage)
        # Retourner le offset de la ligne à la position du chainage
        return interpolateOffsetOnLine(long_d+long, long_f-long_d, offset_d, offset_f)
    
    def isChainageOnRTSS(self, chainage:Union[int, float, Chainage])->bool:
        """ Méthode qui permet de vérifier si le chainage est valide pour le RTSS """
        return self.chainageDebut() <= chainage and self.chainageFin() >= chainage
    
    def isLineOnRTSS(self, line:LineRTSS, partial=False)->bool:
        """
        Permet de définir si la ligne est sur le RTSS.

        Args:
            - line (LineRTSS): La ligne à vérifier
            - partial (bool): Indique si la ligne peux être partiellement sur le RTSS
        """
        if not line.isValide(): return False
        if partial: return self.num_rts in line.listRTSS()
        else: return line.hasOneRTSS() and line.startPoint().getRTSS() == self.num_rts

    def isOnExtremities(self, obj_rtss:Union[PointRTSS, LineRTSS, PolygonRTSS], tolerance=0):
        """
        Permet de vérifier si un objet RTSS se trouve sur une des extremitées du RTSS.

        Args:
            obj_rtss (Union[PointRTSS, LineRTSS, PolygonRTSS]): L'objet RTSS à vérifier
            tolerance (int, optional): Tolérence des chainages. Defaults to 0.
        """
        if isinstance(obj_rtss, PointRTSS): chainages = [obj_rtss.getChainage()]
        elif isinstance(obj_rtss, LineRTSS): chainages = [obj_rtss.startChainage(), obj_rtss.endChainage()]
        elif isinstance(obj_rtss, PolygonRTSS): chainages = [obj_rtss.getChainageDebut(), obj_rtss.getChainageFin()]
        else: return None
        
        if any([c <= self.chainageDebut()+tolerance for c in chainages]): return True
        if any([c >= self.chainageFin()-tolerance for c in chainages]): return True
        return False

    def length(self, in_chainage=False)->float:
        """
        Permet de retourner la longeur du RTSS
        
        Args:
            - in_chainage (bool): Retourner la distance en chainage 
        """
        if in_chainage: return self.chainage_f - self.chainage_d
        else: return self.geometry().length()

    def setChainageDebut(self, chainage:Union[int, float, Chainage, str]):
        """ Permet de définir le chainage de début du RTSS """
        self.chainage_d = Chainage(chainage)

    def setChainageFin(self, chainage:Union[int, float, Chainage]):
        """ Permet de définir le chainage de fin du RTSS """
        # S'assurer que le chainage de fin est plus grand que le chainage de début
        if self.chainage_d >= chainage: 
            raise ValueError("Le chainage de fin doit etre plus grand que le chainage de debut")
        self.chainage_f = Chainage(chainage)

    def side(self, point:Union[QgsPointXY, QgsGeometry]):
        """
        Méthode qui permet de retourner le côté du RTSS par rapport à un point.

        Args:
            point (Union[QgsPointXY, QgsGeometry]): Le point à vérifier

        Returns (int):
            Le côté du RTSS dans le sense du chainage. [1 = Droite] | [-1 = Gauche] | [0 = Centre]
        """
        point = FeatRTSS.verifyFormatPoint(point).asPoint()
        # Trouver les vertex du RTSS à proximité du point (avant, plus proche et après)
        id, vertex_id, previous_vertex_id, nextVertexIndex, sqr_dist = self.geometry().closestVertex(point)
        
        # Verifier si le vertex avant existe donc que le point n'est pas au début complétement de la ligne
        # Trouver le côté (vertex proche => vertex après)
        if previous_vertex_id == -1: return QgsGeometryUtils.segmentSide(
            self.geometry().vertexAt(vertex_id),
            self.geometry().vertexAt(nextVertexIndex),
            QgsPoint(point))
        # Trouver le côté ligne(vertex avant => vertex proche)
        else: return QgsGeometryUtils.segmentSide(
            self.geometry().vertexAt(previous_vertex_id),
            self.geometry().vertexAt(vertex_id),
            QgsPoint(point))

    def verifyFormatPoint(point:Union[QgsPointXY, QgsPoint, QgsGeometry]) -> QgsGeometry:
        """
        Fonction qui permet de toujours renvoyer une geometry (QgsGeometry).

        Args:
            - point (QgsPointXY/QgsPoint/QgsGeometry): Le point à vérifier
        """
        if isinstance(point, QgsPointXY): return QgsGeometry().fromPointXY(point)
        elif isinstance(point, QgsPoint): return QgsGeometry().fromPointXY(QgsPointXY(point))
        else: return point