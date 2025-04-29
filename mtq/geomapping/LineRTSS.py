# -*- coding: utf-8 -*-
from ..fnt.interpolateOffsetOnLine import interpolateOffsetOnLine
from typing import Union
from collections import Counter
from qgis.core import QgsGeometry

# Librairie MTQ
from .RTSS import RTSS
from .PointRTSS import PointRTSS

class LineRTSS:
    """ Définition d'une ligne selon le référencement linéaire RTSS/chainage du MTQ """

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
    def fromChainages(cls, rtss:Union[str, RTSS], list_chainages:list):
        """ 
        Constructueur de l'objet LineRTSS à partir d'une list de chainage et un RTSS

        Args:
            - rtss (RTSS/str): Le RTSS de la ligne
            - list_chainages (list): La liste des chainages de la ligne
        """
        return cls([PointRTSS(rtss, chainage) for chainage in list_chainages])
            
    def __str__ (self): return str(self.points)
    
    def __repr__ (self): return f"LineRTSS {self.points}"

    def __iter__ (self): return self.points.__iter__()

    def __getitem__(self, index)->PointRTSS: return self.points[index]

    def addPoint(self, point:PointRTSS):
        """
        Permet d'ajouter un PointRTSS à la ligne 

        Args:
            - point (PointRTSS): Le point à ajouter
        """
        self.points.append(point)

    def distanceAtVertex(self, vertex: Union[int, PointRTSS]):
        if isinstance(vertex, int): vertex = self.getVertex(vertex)
        # Longueur de la ligne par défault
        longueur = 0
        # Retourne une longueur la ligne par défault si elle n'est pas valide
        if self.isInvalide(): return longueur
        # Définir le dernier point parcouru avec le premier de la ligne 
        last_point = self.startPoint()
        # Parcourir toutes les points de la ligne sauf le premier
        for point in self.points[1:]:
            # Arrêter le calcule
            if vertex == last_point: break
            # TODO: Ajuster le calcule pour prendre en compte les offsets dans le calcule des distances
            if str(point.getRTSS()) == str(last_point.getRTSS()): longueur += abs(float(last_point.getChainage()) - float(point.getChainage()))
            # Conserver le dernier point parcouru
            last_point = point
        return longueur

    def endChainage(self):
        """ Permet de retourner le chainage de fin de la ligne """
        if self.isEmpty(): return None
        else: return self.points[-1].getChainage()

    def endOffset(self):
        """ Permet de retourner le offset de fin de la ligne """
        if self.isEmpty(): return None
        else: return self.points[-1].getOffset()

    def endPoint(self):
        """ Permet de retourner le premier point de la ligne """
        if self.isEmpty(): return None
        else: return self.points[-1]

    def getGeometry(self)->QgsGeometry:
        return self.geom

    def getPoints(self):
        """ Permet de retourner la liste des PointRTSS de la ligne """
        return self.points

    def getRTSS(self):
        """ Permet de retourner le RTSS de la ligne """
        if self.isEmpty(): return None
        return self.points[0].getRTSS()

    def getVertex(self, vertex_id:int):
        """
        Permet de retourner le PointRTSS du vertex à la position dans la ligne.
        
        Args:
            - vertex_id (int): 
        """
        if vertex_id <= len(self.points)-1: return self.points[vertex_id]
        else: return None

    def hasOffset(self):
        """ Permet de vérifier si la ligne à un offset par rapport à la trace """
        for pt in self.points:
            if pt.hasOffset(): return True
        return False

    def hasOneRTSS(self):
        """ Permet de vérifier si la ligne est sur un seul RTSS """
        return True

    def isEmpty(self):
        """ Permet de retourner un indicateur de si la ligne est vide """
        return self.points == []
    
    def isInvalide(self):
        """ Permet de vérifier si la ligne est invalide """
        return not self.isValide()

    def isParallel(self, precision=5):
        """ Permet de vérifier si la ligne est parallel a la trace """
        if self.isInvalide(): return None
        if precision is None: return len(set([pt.getOffset() for pt in self.points])) == 1
        else: return len(set([round(pt.getOffset(), precision)  for pt in self.points])) == 1

    def isValide(self):
        """
        Permet de retourner un indicateur de si la ligne est valide.
        Donc contient plus de 1 chainage différent.
        """
        return len(set(self.points)) > 1

    def interpolate(self):
        """ Indicateur que la ligne doit interpoler la trace du RTSS entre les points """
        return self.interpolate_on_rtss

    def length(self):
        """ Permet de retourner la longueur en chainage de la ligne """
        return self.distanceAtVertex(self.endPoint())

    def listRTSS(self):
        """ Permet de retourner une liste des RTSS de la ligne """
        return list(set([p.getRTSS() for p in self.points]))

    def reverse(self):
        """ Permet de renverser l'ordre des points de la ligne """
        self.points.reverse()

    def setEnd(self, point:PointRTSS):
        """
        Méthode qui permet de définir le dernier point de la ligne

        Args:
            - point(PointRTSS) = Le point à définir comme le dernier
        """
        self.setPoint(idx=-1, point_rtss=point)

    def setInterpolation(self, interpolate_on_rtss):
        """ Permet de définir si la ligne doit être interpolé sur le RTSS """
        self.interpolate_on_rtss = interpolate_on_rtss

    def setGeometry(self, geometry:QgsGeometry):
        """ Permet de définir une attribut de géometrie """
        self.geom = geometry

    def setOffset(self, offset_d:Union[int, float], offset_f:Union[int, float]=None):
        """ 
        Permet de définir un offset pour une ligne. Chaque point est modifier pour représenter la ligne
        selon un offset de début et de fin.
        Le offset de début est appliqué sur toute la ligne si aucun offset de fin n'est défini.

        Args:
            - offset_d (int/float): Le offset de début de la ligne
            - offset_f (int/float): Le offset de fin de la ligne
        """
        # Mettre la ligne parralèle si aucun offset de fin est définie
        if offset_f is None: offset_f = offset_d
        # Définir la longueur total de la ligne
        longueur = self.length()
        # OPTIMISATION: distanceAtVertex fait plusieurs fois la boucle car il reprend toujours au début
        # Parcourir chaque point de la ligne
        for point in self.points:
            # Définir le offset du point constant si la ligne est parralèle 
            if offset_d == offset_f: point.setOffset(offset_d)
            # Définir le offset du point selon le offset de début et de fin
            else: point.setOffset(interpolateOffsetOnLine(
                    dist=self.distanceAtVertex(point),
                    longeur=longueur,
                    offset_d=offset_d,
                    offset_f=offset_f))

    def setPoint(self, idx, point_rtss:PointRTSS):
        """
        Permet de modifier un point de la ligne

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
        Permet de définir la liste des points qui constitue la ligne

        Args:
            - points (list): Liste d'objet PointRTSS
        """
        # Vérifier que les points soient tous sur les mêmes RTSS
        if len(set([pt.getRTSS() for pt in points])) > 1:
            raise Exception("Les points doivent etre sur 1 seul RTSS")
        self.points = points

    def setStart(self, point:PointRTSS):
        """
        Méthode qui permet de définir le premier point de la ligne

        Args:
            - point(PointRTSS) = Le point à définir comme le premier
        """
        self.setPoint(idx=0, point_rtss=point)

    def startChainage(self):
        """ Permet de retourner le chainage de début de la ligne """
        if self.isEmpty(): return None
        else: return self.points[0].getChainage()

    def startOffset(self):
        """ Permet de retourner le offset de début de la ligne """
        if self.isEmpty(): return None
        else: return self.points[0].getOffset()

    def startPoint(self):
        """ Permet de retourner le premier point de la ligne """
        if self.isEmpty(): return None
        else: return self.points[0]

    def side(self):
        """
        Permet de retourner le côté de la ligne le plus fréquent en terme de nombre de points.
        
        Return: Le côté le plus fréquent (1 = Droite, -1 = Gauche, 0 = Centre)
        """
        if self.startOffset() == 0 and self.endOffset() == 0: return 0
        # Liste des côtés des points de la ligne
        sides = [pt.side() for pt in self.points if pt.side() != 0]
        if not sides: return None
        # Retourner le côté le plus fréquent
        return Counter(sides).most_common(1)[0][0]
    
    def toSensChainage(self, reverse=False):
        """
        Permet de réorganiser les chainages de la ligne dans la direction du chainage

        Args:
            reverse (bool, optional): Inverser la direction. Defaults to False.
        """
        self.points = sorted(self.points, key=lambda p: p.getChainage(), reverse=reverse)