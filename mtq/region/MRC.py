# -*- coding: utf-8 -*-
from typing import Union
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem
from .Region import Region
from .Municipalite import Municipalite

class MRC(Region):
    """ Object représentant une région de Municipalité régionale de compté (MRC) """
    
    __slots__ = ("region_name", "region_code", "dict_mun", "geom", "region_crs", "z_fill")

    def __init__(self,
                 mrc_code:Union[str, int],
                 mrc_name:str,
                 geom:QgsGeometry=None,
                 crs:QgsCoordinateReferenceSystem=None):
        Region.__init__(
            self,
            region_code=mrc_code,
            region_name=mrc_name,
            geom=geom,
            crs=crs)
        self.dict_mun:dict[int, Municipalite] = {}
    
    def __str__ (self): return f"{self.name()} ({self.code(as_string=True)})"
    
    def __repr__ (self): return f"MRC: {self.name()} ({self.code(as_string=True)})"

    def __iter__(self): return self.dict_mun.values().__iter__()

    def __contains__(self, key):
        return self.getMunicipalite(key) is not None

    def addMunicipalite(self, mun:Municipalite):
        """ Méthode qui permet d'ajouter un objet Municipalite a l'interieur de la MRC """
        if mun.code() in self.dict_mun: return False
        self.dict_mun[mun.code()] = mun
        return True
    
    def getMunicipalite(self, value):
        """ Permet de retourner l'objet Municipalite selon un code ou un nom """
        for mun in self:
            if mun == value: return mun
        return None

    def getListNameMunicipalite(self):
        """ Retourne une list des noms des Municipalite présents dans la MRC """
        return [mun.name() for mun in self]

