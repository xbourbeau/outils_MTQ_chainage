# -*- coding: utf-8 -*-
from ..functions.reprojections import reprojectGeometry
from typing import Union
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem
from .Region import Region

class Municipalite(Region):
    """ Object représentant une région municipale """
    
    __slots__ = ("region_name", "region_code", "geom", "region_crs", "z_fill")

    def __init__(self,
                 cs_code:Union[str, int],
                 cs_name:str,
                 geom:QgsGeometry=None,
                 crs:QgsCoordinateReferenceSystem=None):
        Region.__init__(
            self,
            region_code=cs_code,
            region_name=cs_name,
            geom=geom,
            crs=crs,
            z_fill=5)
    
    def __str__ (self): return f"{self.name()} ({self.code(as_string=True)})"
    
    def __repr__ (self): return f"Municipalite: {self.name()} ({self.code(as_string=True)})"

