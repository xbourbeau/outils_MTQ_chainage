# -*- coding: utf-8 -*-
from ..fnt.reprojections import reprojectGeometry
from typing import Union
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem

class Region:
    """ Object représentant une région administrative """
    
    __slots__ = ("region_name", "region_code", "geom", "region_crs", "z_fill")

    def __init__(self,
                 region_code:Union[str, int],
                 region_name:str,
                 geom:QgsGeometry=None,
                 crs:QgsCoordinateReferenceSystem=None,
                 z_fill=2):
        # Définir les pramètres de l'oject région
        self.setCode(region_code)
        self.setName(region_name)
        self.setGeometry(geom, crs)
        self.z_fill = z_fill

    def __str__ (self): return f"{self.name()} ({self.code(as_string=True)})"
    
    def __repr__ (self): return f"Region: {self.name()} ({self.code(as_string=True)})"

    def __eq__(self, other):
        if isinstance(other, Region): return self.name() == other.name()
        else: 
            try:
                if self.code() == other: return True
                if self.code(as_string=True) == other: return True
                if self.name().lower() == str(other).lower(): return True
            except: return False

    def __ne__(self, other):
        if isinstance(other, Region): return self.code() != other.code()
        else: 
            try: return all([
                    self.code() != other,
                    self.code(as_string=True) != other,
                    self.name().lower() != str(other).lower()])
            except: return False

    def code(self, as_string=False):
        """ Méthode qui retourne le code de la région """
        if as_string: return str(self.region_code).zfill(self.z_fill)
        return self.region_code

    def name(self):
        """ Méthode qui retourne le nom de la région """
        return self.region_name

    def geometry(self)->QgsGeometry:
        """ Méthode qui retourne la géométrie de la région """
        return self.geom

    def contains(self, geom_to_check, crs:QgsCoordinateReferenceSystem=None)->bool:
        """ Méthode qui permet de vérifie si une géométrie est dans la région """
        # Reprojecter la geometrie dans le même système de coordonnées si 2 projection sont défini
        if self.crs() and crs: geom_to_check = reprojectGeometry(geom_to_check, crs, self.crs())
        # Retrouner VRAI ou FAUX selon l'intersection
        if self.geometry().boundingBoxIntersects(geom_to_check): return self.geometry().intersects(geom_to_check)
        return False

    def crs(self)->QgsCoordinateReferenceSystem:
        """ Permet de routrner le QgsCoordinateReferenceSystem de la géometry """
        return self.region_crs

    def setCode(self, region_code:Union[str, int]):
        """ Méthode pour définir le code de la région """
        self.region_code = int(region_code)

    def setName(self, region_name:str):
        """ Méthode pour définir le nom de la région """
        self.region_name = region_name

    def setGeometry(self, geom:QgsGeometry, crs:QgsCoordinateReferenceSystem=None):
        """ Méthode pour définir une geometry et un projection pour la région """
        self.geom = geom
        self.region_crs = crs


