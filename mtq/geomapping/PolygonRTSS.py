# -*- coding: utf-8 -*-
from ..functions.interpolateOffsetOnLine import interpolateOffsetOnLine
from ..functions.identifyPolygonCorners import identifyPolygonCorners
from ..functions.groupeValues import groupeValues
from ..functions.getCenterPoint import getCenterPoint
# Importer la librairie pour des opérations trigo
from typing import Union
from collections import Counter
import numpy as np

from qgis.core import QgsGeometry

try:
    from shapely.geometry import Polygon, LineString
    from shapely.ops import unary_union
except: pass

# Librairie MTQ
from .RTSS import RTSS
from .PointRTSS import PointRTSS
from .LineRTSS import LineRTSS

class PolygonRTSS:
    """ Définition d'un polygon selon le référencement linéaire RTSS/chainage du MTQ """

    __slots__ = ("points", "interpolate_on_rtss", "geom")
    
    def __init__ (self, points:list[PointRTSS]=[], interpolate_on_rtss=True):
        """
        Constructeur de l'objet LineRTSS
        Une ligne peut être sur plus d'un RTSS, mais un point devrait être doubler au changement de RTSS.

        Args:
            - points (list): Liste d'objet PointRTSS
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points
        """
        self.setPoints(points)
        self.setInterpolation(interpolate_on_rtss)
        self.setGeometry(None)
    
    @classmethod
    def fromChainages(cls, rtss:Union[str, RTSS], list_chainages:list, list_offsets:list, interpolate_on_rtss=True):
        """ 
        Constructueur de l'objet PolygonRTSS sur un RTSS à partir
        d'une liste de chainage et de offset.

        Args:
            - rtss (RTSS/str): Le RTSS de la ligne
            - list_chainages (list): La liste des chainages de la ligne
            - list_offsets (list): La liste des offsets de la ligne
            - interpolate_on_rtss (bool): Interpoler la trace du RTSS entre les points
        """
        return cls(
            points=[PointRTSS(rtss, c, o) for c, o in zip(list_chainages, list_offsets)],
            interpolate_on_rtss=interpolate_on_rtss)
            
    def __str__ (self): return str(self.points)
    
    def __repr__ (self): return f"PolygonRTSS {self.points}"

    def __iter__ (self): return self.points.__iter__()

    def __getitem__(self, index): return self.points[index]

    def addPoint(self, point:PointRTSS):
        """
        Permet d'ajouter un PointRTSS au polygone 

        Args:
            - point (PointRTSS): Le point à ajouter
        """
        self.points.append(point)

    def createMidleLine(self, tolerance_angle=170):
        """ 
        Méthode qui permet de retourner la ligne de centre d'un polygon.
        
        Args: 
            tolerance_angle (int) = L'angle max pour être considérer un coin du polygon

        Return (LineRTSS): Une ligne RTSS qui représente le milieu du polygon
        """
        # Liste des coordonnées (chainage, offset) du polygone
        pts_coords = [(i.getChainage().value(), i.getOffset()) for i in self.getPoints()][:-1]
        # Identifier les coins du polygon
        chainages, offsets = zip(*identifyPolygonCorners(pts_coords, tolerance_angle=tolerance_angle))
        # Identifier les débuts fin du polygon
        # BUGS: Il faut tester si la librairie est installer
        labels = groupeValues(chainages)
        # Identifier le numéro du groupe qui représente le chainage de début
        start_nbr = labels[chainages.index(min(chainages))]
        # Séparer les coordonnées des coins du début
        start_coords = [(chainages[i], offsets[i]) for i in range(len(labels)) if labels[i] == start_nbr]
        # Séparer les coordonnées des coins de la fin
        end_coords = [(chainages[i], offsets[i]) for i in range(len(labels)) if labels[i] != start_nbr]
        # Définir les valeurs de début de la ligne milieu
        chainage_d, offset_d = getCenterPoint(start_coords)
        # Définir les valeurs de fin de la ligne milieu
        chainage_f, offset_f = getCenterPoint(end_coords)
        # Retourner la ligne milieu
        return LineRTSS([
            PointRTSS(self.getRTSS(), chainage_d, offset_d),
            PointRTSS(self.getRTSS(), chainage_f, offset_f)])

    def getChainageDebut(self):
        """ Permet de retourner le chainage le plus petit """
        return min([pt.getChainage() for pt in self.points])
    
    def getChainageFin(self):
        """ Permet de retourner le chainage le plus grand """
        return max([pt.getChainage() for pt in self.points])
    
    def getCoordiantes(self):
        """ Permet de retourner les coordonnées du polygon """
        return [(pt.getChainage().value(), pt.getOffset()) for pt in self.points]
    
    def getOffsetMax(self):
        """ Permet de retourner le offset le plus petit """
        return max([pt.getOffset() for pt in self.points])

    def getOffsetMin(self):
        """ Permet de retourner le offset le plus grand """
        return min([pt.getOffset() for pt in self.points])

    def getHeight(self):
        """ Permet de retourner la différente maximum des offsets des points du polygon """
        offsets = [pt.getOffset() for pt in self.points]
        return abs(min(offsets) - max(offsets))
    
    def getGeometry(self)->QgsGeometry:
        return self.geom

    def calculerLargeur(self):
        """
        Calculate the average width of a polygon by sampling multiple cross-sections.
        
        Args:
            polygon_coords: List of (x, y) tuples representing polygon vertices
            
        Returns:
            float: Average width of the polygon
        """
        # Create Shapely polygon
        poly = Polygon(self.getCoordiantes())
        # Get the minimum rotated rectangle
        minbox = poly.minimum_rotated_rectangle
        
        # Get the major axis (longest side) of the minimum bounding rectangle
        coords = np.array(minbox.exterior.coords)
        distances = np.sqrt(np.sum((coords[:-1] - coords[1:]) ** 2, axis=1))
        major_axis_length = max(distances)
        
        # Create evenly spaced points along the major axis
        num_samples = int(self.getWidth()) * 2
        major_axis = sorted([(p1, p2) for p1, p2 in zip(coords[:-1], coords[1:])], 
                        key=lambda x: np.sqrt(np.sum((x[0] - x[1]) ** 2)))[-1]
        start_point, end_point = major_axis
        sample_points = np.linspace(start_point, end_point, num_samples)
        
        # Calculate perpendicular lines and their intersections
        widths = []
        for point in sample_points:
            # Calculate perpendicular direction
            direction = np.array([-(end_point[1] - start_point[1]), 
                                end_point[0] - start_point[0]])
            direction = direction / np.sqrt(np.sum(direction ** 2))
            
            # Create a line that's guaranteed to cross the entire polygon
            line_length = major_axis_length * 2
            line_start = point + direction * line_length
            line_end = point - direction * line_length
            
            # Create line and get intersection
            line = LineString([line_start, line_end])
            intersection = line.intersection(poly)
            
            if not intersection.is_empty:
                if isinstance(intersection, LineString):
                    width = intersection.length
                    widths.append(width)
        
        return float(np.mean(widths)) if widths else 0

    def getPoints(self):
        """ Permet de retourner la liste des PointRTSS du polygon """
        return self.points

    def getRTSS(self):
        """ Permet de retourner le RTSS du polygone """
        return self.listRTSS()[0]

    def getWidth(self):
        """ Permet de retourner la différente maximum des chainages des points du polygon """
        chainages = [pt.getChainage().value() for pt in self.points]
        return abs(min(chainages) - max(chainages))

    def hasOneRTSS(self):
        """ Permet de vérifier si le polygon est sur un seul RTSS """
        return True

    def isEmpty(self):
        """ Permet de retourner un indicateur de si la ligne est vide """
        return self.points == []
    
    def isValide(self):
        """
        Permet de retourner un indicateur de si le polygon est valide.
        Donc s'il contient au moins 3 points.
        """
        if self.isEmpty(): return False
        return self.pointCount() > 3 and self.points[0] == self.points[-1]
    
    def interpolate(self):
        """ Indicateur que le polygon doit interpoler la trace du RTSS entre les points """
        return self.interpolate_on_rtss

    def listRTSS(self):
        """ Permet de retourner une liste des RTSS du polygon """
        return list(set([p.getRTSS() for p in self.points]))
    
    def pointCount(self):
        """ Permet de retourner le nombre de point du polygon """
        return len(self.points)

    def setInterpolation(self, interpolate_on_rtss):
        """ Permet de définir si le polygon doit être interpolé sur le RTSS """
        self.interpolate_on_rtss = interpolate_on_rtss

    def setGeometry(self, geometry:QgsGeometry):
        """ Permet de définir une attribut de géometrie """
        self.geom = geometry

    def setPoint(self, idx, point_rtss:PointRTSS):
        """
        Permet de modifier un point du polygon

        Args:
            idx (int): L'index du point a modifier
            point_rtss (PointRTSS): Le point modifié
        """
        # Vérifier que le point est sur le même RTSS
        if self.getRTSS() != point_rtss.getRTSS(): raise Exception(f"Le point doit etre sur le RTSS {self.getRTSS().valueFormater()}")
        try: self.points[idx] = point_rtss
        except: return False
        return True

    def setPoints(self, points:list[PointRTSS]):
        """ 
        Permet de définir la liste des points qui constitue le polygone.
        Si le dernier point n'est pas le même que le premier, celui-ci vas être
        ajouter pour fermer le polygon

        Args:
            - points (list): Liste d'objet PointRTSS
        """
        if points != []:
            if points[0] != points[-1]: points.append(points[0])
        self.points = points

    def side(self):
        """ 
        Permet de retourner le côté de la ligne le plus fréquent en terme de nombre de points
        
        Return: Le côté le plus fréquent (1 = Droite, -1 = Gauche, 0 = Centre)
        """
        # Liste des côtés des points de la ligne
        sides = [pt.side() for pt in self.points if pt.side() != 0]
        if not sides: return None
        # Retourner le côté le plus fréquent
        return Counter(sides).most_common(1)[0][0]