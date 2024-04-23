# -*- coding: utf-8 -*-
from ..fnt.interpolateOffsetOnLine import interpolateOffsetOnLine
# Importer la librairie pour des opérations trigo
from typing import Union

# Librairie MTQ
from .RTSS import RTSS
from .PointRTSS import PointRTSS

class PolygonRTSS:
    """ Définition d'un polygon selon le référencement linéaire RTSS/chainage du MTQ """

    __slots__ = ("points", "interpolate_on_rtss")
    
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
    
    def __repr__ (self): return f"PolygonRTSS {self.points}"

    def __iter__ (self): return self.points.__iter__()

    def __getitem__(self, index): return self.points[index]

    def createMidleLine(self):
        """
        Méthode qui permet de retourner la ligne de centre d'un polygon 
        """
        # TODO: Développer la méthode
        pass

    def getPoints(self):
        """ Permet de retourner la liste des PointRTSS du polygon """
        return self.points

    def hasOneRTSS(self):
        """ Permet de vérifier si le polygon est sur un seul RTSS """
        return len(self.listRTSS()) == 1

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