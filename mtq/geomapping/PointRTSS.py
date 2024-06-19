# -*- coding: utf-8 -*-
# Importer les objects du module core de QGIS 
from qgis.core import QgsGeometry
from typing import Union

# Librairie MTQ
from .Chainage import Chainage
from .RTSS import RTSS

class PointRTSS:
    """ Une définition d'un point selon le référencement linéaire RTSS/chainage du MTQ"""
    
    __slots__ = ("rtss", "chainage", "offset", "geom")
    
    def __init__ (self, rtss:Union[int, RTSS], chainage:Union[int, Chainage, float], offset:Union[int, float]=0):
        """
        Constructeur de l'objet PointRTSS
        
        Args:
            - rtss (RTSS/str): Le RTSS du point
            - chainage (Chainage/real): Le chainage du point sur le RTSS
            - offset (real): La distance trace du point 
        """
        self.setRTSS(rtss)
        self.setChainage(chainage)
        self.setOffset(offset)
        self.setGeometry(None)
    
    def __str__ (self): return f"PointRTSS {self.rtss}: {self.chainage}, {self.offset}m"
    
    def __repr__ (self): return f"PointRTSS {self.rtss}: {self.chainage} ({self.offset}m)"

    def getChainage(self, **kwargs):
        """
        Permet de retourner l'objet Chainage
        Les paramètres peuvent être spécifier pour retourner le Chainage sous forme de text/chiffre
        
        Args:
            - formater (bool): Indique si le chainage retourné doit être formater
            - precision (int): Précision du chainage à retourner
        """
        if "formater" in kwargs or "precision" in kwargs: return self.chainage.value(**kwargs)
        return self.chainage
        
    def getGeometry(self)->QgsGeometry:
        return self.geom

    def getOffset(self):
        """ Permet de retourner la distance de offset """
        return self.offset
    
    def getRTSS(self, **kwargs):
        """
        Permet de retourner l'objet RTSS.
        Les paramètres peuvent être spécifier pour retourner le RTSS sous forme de text
        
        Args:
            - formater (bool): Indique si le RTSS retourné doit être formater
            - zero (bool): Conserver les zéro au début
        """
        if "formater" in kwargs or "zero" in kwargs: return self.rtss.value(**kwargs)
        return self.rtss

    def hasOffset(self):
        """ Permet de vérifier si le point à un offset """
        return self.offset != 0

    def setChainage(self, chainage):
        self.chainage = Chainage(chainage)

    def setGeometry(self, geometry:QgsGeometry):
        """ Permet de définir une attribut de géometrie """
        self.geom = geometry

    def setOffset(self, offset):
        self.offset = offset
    
    def setRTSS(self, rtss):
        self.rtss = RTSS(rtss)
