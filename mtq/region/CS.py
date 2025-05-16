# -*- coding: utf-8 -*-
from ..functions.reprojections import reprojectGeometry
from typing import Union
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem
from .Region import Region
from .Municipalite import Municipalite

class CS(Region):
    """ Object représentant une région d'un centre de services du MTQ """
    
    __slots__ = ("region_name", "region_code", "dict_mun", "geom", "region_crs", "prefix", "z_fill")

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
            crs=crs)
        # Définir les paramètres de l'oject CS
        self.dict_mun:dict[int, Municipalite] = {}
        # List des préfix possible pour le nom du CS
        self.prefix = ("CS des ", "CS de ", "CS d' ")
    
    def __str__ (self): return f"{self.name()} ({self.code(as_string=True)})"
    
    def __repr__ (self): return f"CS: {self.name()} ({self.code(as_string=True)})"

    def __iter__(self): return self.dict_mun.values().__iter__()

    def __eq__(self, other):
        if isinstance(other, CS): return self.name() == other.name()
        else: 
            try:
                if self.code() == other: return True
                if self.code(as_string=True) == other: return True
                if self.name("court").lower() == str(other).lower(): return True
                if self.name("complet").lower() == str(other).lower(): return True
                if self.name("long").lower() == str(other).lower(): return True
            except: return False

    def __ne__(self, other):
        if isinstance(other, CS): return self.code() != other.code()
        else: 
            try: return all([
                    self.code() != other,
                    self.code(as_string=True) != other,
                    self.name("court").lower() != str(other).lower(),
                    self.name("court").lower() != str(other).lower(),
                    self.name("court").lower() != str(other).lower()])
            except: return False

    def __contains__(self, key):
        return self.getMunicipalite(key) is not None

    def addMunicipalite(self, mun:Municipalite):
        """ Méthode qui permet d'ajouter un objet Municipalite a l'interieur du CS """
        if mun.code() in self.dict_mun: return False
        self.dict_mun[mun.code()] = mun
        return True
    
    def getMunicipalite(self, value):
        """ Permet de retourner l'objet Municipalite selon un code ou un nom """
        for mun in self:
            if mun == value: return mun
        return None

    def getListNameMunicipalite(self):
        """ Retourne une list des noms des municipalitées présents dans le CS """
        return [mun.name() for mun in self]

    # Méthode qui retourne le nom du CS
    def name(self, type="court")->str:
        """
        Méthode qui permet de retourner le nom du CS
        Le type peux être définie dépendament du prévix de CS à avoir.
            - court = Aucun préfix ex. "Foster"
            - complet = Le préfixe complet ex. "Centre de services de Foster"
            - long = Le préfixe abrégé ex. "CS de Foster"

        Args:
            - type (str): Choix du type de nom à recevoire [court, complet, long]
        """
        # Retroune le nom complet avec préfix
        if type == "complet": return self.region_name.replace("CS", 'Centre de services')
        elif type == "long": return self.region_name
        # Retire le préfix du nom
        else:
            name = self.region_name
            for s in self.prefix: 
                name = name.replace(s, '')
            return name

