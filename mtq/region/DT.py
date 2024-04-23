# -*- coding: utf-8 -*-
from ..fnt.reprojections import reprojectGeometry
from typing import Union
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem
from .Region import Region
from .CS import CS

class DT (Region):
    """ Object représentant les directions territoriale du MTQ """
    
    __slots__ = ("region_name", "region_code", "dict_cs", "geom", "region_crs", "prefix", "z_fill")
    
    def __init__(self,
                 dt_code:Union[str, int],
                 dt_name:str,
                 geom:QgsGeometry=None,
                 crs:QgsCoordinateReferenceSystem=None):
        Region.__init__(self, dt_code, dt_name, geom, crs)
        # Définir les pramètres de l'oject DT
        self.dict_cs:dict[int, CS] = {}
        # List des préfix possible pour le nom de la DT
        self.prefix = ("DG de l'", "DG de la ", "DG du ", "DG des ", "DG d'")
    
    def __str__ (self): return f"{self.name()} ({self.code(as_string=True)})"
    
    def __repr__ (self): return f"DT: {self.name()} ({self.code(as_string=True)})"

    def __iter__(self): return self.dict_cs.values().__iter__()

    def __eq__(self, other):
        if isinstance(other, DT): return self.code() == other.code()
        else: 
            try:
                if self.code() == other: return True
                if self.code(as_string=True) == other: return True
                if self.name("court").lower() == str(other).lower(): return True
                if self.name("complet").lower() == str(other).lower(): return True
                if self.name("long").lower() == str(other).lower(): return True
            except: return False

    def __ne__(self, other):
        if isinstance(other, DT): return self.code() != other.code()
        else: 
            try: return all([
                    self.code() != other,
                    self.code(as_string=True) != other,
                    self.name("court").lower() != str(other).lower(),
                    self.name("court").lower() != str(other).lower(),
                    self.name("court").lower() != str(other).lower()])
            except: return False

    def __contains__(self, key):
        cs = self.getCS(key)
        return cs is not None

    def addCS(self, cs:CS):
        """ Méthode qui permet d'ajouter un objet Region a l'interieur de la DT """
        if cs.code() in self.dict_cs: return False
        self.dict_cs[cs.code()] = cs
        return True
    
    def getCS(self, value):
        """ Permet de retourner l'objet CS selon un code ou un nom """
        for cs in self:
            if cs == value: return cs
        return None

    def getListCodeCS(self):
        """ Méthode qui permet de retourner une liste des codes de CS de la DT """
        return list(self.dict_cs.keys())
    
    def getListCS(self):
        """ Méthode qui permet de retourner une liste des objet CS de la DT """
        return list(self.dict_cs.values())

    def getListNameCS(self, type="court"):
        """ Retourne une list des noms des cs présents dans le dt """
        return [cs.name(type=type) for cs in self]

    def name(self, type="court"):
        """
        Méthode qui permet de retourner le nom de la DT
        Le type peux être définie dépendament du prévix de DT à avoir.
            - court = Aucun préfix ex. "Estrie"
            - complet = Le préfixe complet ex. "Direction générale de l'Estrie"
            - long = Le préfixe abrégé ex. "DT de l'Estrie"

        Args:
            - type (str): Choix du type de nom à recevoire [court, complet, long]
        """
        # Retroune le nom complet avec préfix
        if type == "complet": return self.region_name.replace("DG", 'Direction générale')
        elif type == "long": return self.region_name
        # Retire le préfix du nom
        else:
            name = self.region_name
            for s in self.prefix: name = name.replace(s, '')
            return name