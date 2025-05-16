# -*- coding: utf-8 -*-
from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem, QgsVectorLayer
from typing import Union
from ..functions.layer import validateLayer
from .Region import Region
from .CS import CS
from .DT import DT
from .Municipalite import Municipalite
from .MRC import MRC

from ..param import (DEFAULT_NOM_COUCHE_CS, DEFAULT_NOM_CHAMP_CODE_CS,
                    DEFAULT_NOM_CHAMP_NOM_CS, DEFAULT_NOM_CHAMP_CS_CODE_DT,
                    DEFAULT_NOM_COUCHE_DT, DEFAULT_NOM_CHAMP_CODE_DT,
                    DEFAULT_NOM_CHAMP_NOM_DT, DICT_PROVINCE, DEFAULT_NOM_CHAMP_CODE_MUN,
                    DEFAULT_NOM_CHAMP_NOM_MUN, DEFAULT_NOM_COUCHE_MUN, DEFAULT_NOM_COUCHE_MRC,
                    DEFAULT_NOM_CHAMP_CODE_MRC, DEFAULT_NOM_CHAMP_NOM_MRC, DEFAULT_NOM_CHAMP_MUN_CODE_MRC)

class Province(Region):
    """ Object représentant la province du Québec """
    
    __slots__ = ("region_name", "region_code", "dict_dt", "dict_mrc", "geom", "region_crs", "z_fill")

    def __init__(self,
                 prov_code:Union[str, int],
                 prov_name:str,
                 geom:QgsGeometry=None,
                 crs:QgsCoordinateReferenceSystem=None):
        Region.__init__(self, prov_code, prov_name, geom, crs)
        # Définir le dictionnaire des objet DT contenue dans la Province
        self.dict_dt:dict[int, DT] = {}
        # Définir le dictionnaire des objet MRC contenue dans la Province
        self.dict_mrc:dict[int, MRC] = {}
    
    @classmethod
    def fromLayer(cls,
                  layer_dt:QgsVectorLayer,
                  layer_cs:QgsVectorLayer=None,
                  layer_mun:QgsVectorLayer=None,
                  layer_mrc:QgsVectorLayer=None,
                  champ_code_dt=DEFAULT_NOM_CHAMP_CODE_DT,
                  champ_nom_dt=DEFAULT_NOM_CHAMP_NOM_DT,
                  champ_code_cs=DEFAULT_NOM_CHAMP_CODE_CS,
                  champ_nom_cs=DEFAULT_NOM_CHAMP_NOM_CS,
                  champ_cs_code_dt=DEFAULT_NOM_CHAMP_CS_CODE_DT,
                  champ_code_mrc=DEFAULT_NOM_CHAMP_CODE_MRC,
                  champ_nom_mrc=DEFAULT_NOM_CHAMP_NOM_MRC,
                  champ_code_mun=DEFAULT_NOM_CHAMP_CODE_MUN,
                  champ_nom_mun=DEFAULT_NOM_CHAMP_NOM_MUN,
                  champ_mun_code_mrc=DEFAULT_NOM_CHAMP_MUN_CODE_MRC):
        """ Constructeur des CS et DT dans l'objet Province a partir des couches """
        # Créer un objet Province
        prov = cls(53, "Québec")
        # Parcourir les features DT de la couche
        for feat_dt in layer_dt.getFeatures():
            # Ajouter la DT à la Province
            prov.addDT(DT(feat_dt[champ_code_dt], feat_dt[champ_nom_dt], feat_dt.geometry(), layer_dt.crs()))
        
        # Ajouter les MRC
        if layer_mrc is not None:
            # Parcourir les features MRC de la couche
            for feat_mrc in layer_mrc.getFeatures():
                # Ajouter la MRC à la Province
                prov.addMRC(MRC(feat_mrc[champ_code_mrc], feat_mrc[champ_nom_mrc], feat_mrc.geometry(), layer_mrc.crs()))

        # Ajouter les CS
        if layer_cs is not None:
            # Parcourir les features CS de la couche
            for feat_cs in layer_cs.getFeatures():
                # Définir la DT du CS
                dt = prov.getDT(feat_cs[champ_cs_code_dt])
                # Ajouter le CS à la DT de la Province si la DT à été ajouté
                if dt: dt.addCS(CS(feat_cs[champ_code_cs], feat_cs[champ_nom_cs], feat_cs.geometry(), layer_cs.crs()))
              
        # Ajouter les Municipalitées
        if layer_mun is not None:
            # Parcourir les features Municipalité de la couche
            for feat_mun in layer_mun.getFeatures():
                mun = Municipalite(feat_mun[champ_code_mun], feat_mun[champ_nom_mun], feat_mun.geometry(), layer_mun.crs())
                mun_centroid = feat_mun.geometry().centroid()
                # Ajouter la municipalité au CS qui intersect le centroids de la municipalité
                for cs in prov.getCSByIntersection(mun_centroid): cs.addMunicipalite(mun)
                # Ajouter la municipalité à la MRC
                mrc = prov.getMRC(feat_mun[champ_mun_code_mrc])
                if mrc: mrc.addMunicipalite(mun)

        return prov
    
    @classmethod
    def fromMemory(cls):
        """ Constructeur des CS et DT dans l'objet Province a partir du dictionnaire par défault """
        # Créer un objet Province
        prov = cls(53, "Québec")
        # Parcourir les DT du dictionnaire
        for code_dt, dt in DICT_PROVINCE.items():
            # Créer une DT
            obj_dt = DT(code_dt, dt["DT"])
            # Ajouter les CS du dictionnaire à la DT
            for code_cs, nom_cs in dt["CS"].items(): obj_dt.addCS(CS(code_cs, nom_cs))
            # Ajouter la DT à la Province
            prov.addDT(obj_dt)
        return prov

    @classmethod
    def fromProject(cls,
                  layer_dt_name=DEFAULT_NOM_COUCHE_DT,
                  layer_cs_name=DEFAULT_NOM_COUCHE_CS,
                  layer_mun_name=DEFAULT_NOM_COUCHE_MUN,
                  layer_mrc_name=DEFAULT_NOM_COUCHE_MRC,
                  champ_code_dt=DEFAULT_NOM_CHAMP_CODE_DT,
                  champ_nom_dt=DEFAULT_NOM_CHAMP_NOM_DT,
                  champ_code_cs=DEFAULT_NOM_CHAMP_CODE_CS,
                  champ_nom_cs=DEFAULT_NOM_CHAMP_NOM_CS,
                  champ_cs_code_dt=DEFAULT_NOM_CHAMP_CS_CODE_DT,
                  champ_code_mrc=DEFAULT_NOM_CHAMP_CODE_MRC,
                  champ_nom_mrc=DEFAULT_NOM_CHAMP_NOM_MRC,
                  champ_code_mun=DEFAULT_NOM_CHAMP_CODE_MUN,
                  champ_nom_mun=DEFAULT_NOM_CHAMP_NOM_MUN,
                  champ_mun_code_mrc=DEFAULT_NOM_CHAMP_MUN_CODE_MRC):
        """ Constructeur des CS et DT dans l'objet Province a partir du projet """
        # Définir et la couche des DT dans le projet
        layer_dt = validateLayer(layer_dt_name, [champ_code_dt, champ_nom_dt], geom_type=2)
        # Définir et la couche des CS dans le projet
        layer_cs = validateLayer(layer_cs_name, [champ_code_cs, champ_nom_cs, champ_cs_code_dt], geom_type=2)
        # Définir et la couche des MRC dans le projet
        layer_mrc = validateLayer(layer_mrc_name, [champ_code_mrc, champ_nom_mrc], geom_type=2)
        # Définir et la couche des CS dans le projet
        layer_mun = validateLayer(layer_mun_name, [champ_code_mun, champ_nom_mun, champ_mun_code_mrc], geom_type=2)
        # Créer un objet Province avec les couches s'il sont valide
        if layer_dt: return cls.fromLayer(
            layer_dt=layer_dt,
            layer_cs=layer_cs,
            layer_mun=layer_mun,
            layer_mrc=layer_mrc,
            champ_code_dt=champ_code_dt,
            champ_nom_dt=champ_nom_dt,
            champ_code_cs=champ_code_cs,
            champ_nom_cs=champ_nom_cs,
            champ_cs_code_dt=champ_cs_code_dt,
            champ_code_mrc=champ_code_mrc,
            champ_nom_mrc=champ_nom_mrc,
            champ_code_mun=champ_code_mun,
            champ_nom_mun=champ_nom_mun,
            champ_mun_code_mrc=champ_mun_code_mrc)
        # Sinon retourner un objet Province vide
        return cls(53, "QuébecEmpty")

    def __str__ (self): return f"{self.name()} ({self.code(as_string=True)})"
    
    def __repr__ (self): return f"Province: {self.name()} ({self.code(as_string=True)})"

    def __iter__(self): return self.dict_dt.values().__iter__()

    def __contains__(self, key):
        return self.getDT(key) is not None
 
    def addDT(self, dt:DT):
        """ Méthode qui permet d'ajouter un objet DT a l'interieur de la Province """
        if dt.code() in self.dict_dt: return False
        self.dict_dt[dt.code()] = dt
        return True
    
    def addMRC(self, mrc:MRC):
        """ Méthode qui permet d'ajouter un objet MRC a l'interieur de la Province """
        if mrc.code() in self.dict_mrc: return False
        self.dict_mrc[mrc.code()] = mrc
        return True

    def getRegion(self, geom:QgsGeometry, proj:QgsCoordinateReferenceSystem=None)->dict[str, list]:
        """
        Permet de retourner une liste des DT est des CS qui intersect une geometry.
        La geometry est assummée dans la même projection que les régions si la projection est None.

        Args:
            - geom (QgsGeometry): la géometry à comparer avec les régions
            - proj (QgsCoordinateReferenceSystem): Le sytème de coordonner de la géometry
        
        return: Un dictionnaire des DT est CS
        """
        list_dt:list[DT] = self.getDTByIntersection(geom, proj)
        list_mrc:list[MRC] = self.getMRCByIntersection(geom, proj)
        # Liste des objet CS
        list_cs:list[CS] = []
        # Ajouter les CS qui intersect la géometrie
        for dt in list_dt: list_cs.extend([cs for cs in dt if cs.contains(geom, proj)])
        # Liste des objet Municipalite
        list_mun:list[Municipalite] = []
        # Ajouter la liste des Municipalité qui intersect la géometrie
        for cs in list_cs: list_mun.extend([mun for mun in cs if mun.contains(geom, proj)])
        # Vérifier par MRC si aucune municipalité a été trouvé
        if list_mun == []:
            # Ajouter la liste des Municipalité qui intersect la géometrie
            for mrc in list_mrc: list_mun.extend([mun for mun in mrc if mun.contains(geom, proj)])

        return {"DT":list_dt, "CS":list_cs, "MRC":list_mrc, "Mun":list_mun}

    def getDTByIntersection(self, geom:QgsGeometry, proj:QgsCoordinateReferenceSystem=None)->list[DT]:
        """ Méthode qui retourn une liste des DT qui intersectes avec la géométrie rentrée """
        return [dt for dt in self.dict_dt.values() if dt.contains(geom, proj)]
    
    def getCSByIntersection(self, geom:QgsGeometry, proj:QgsCoordinateReferenceSystem=None, filter_dt=None)->list[CS]:
        """ Méthode qui retourn une liste des CS qui intersectes avec la géométrie rentrée """
        # Liste des objet CS
        list_cs = []
        # Parcourir la liste des DT qui intersect la géometrie
        for dt in self.getDTByIntersection(geom, proj):
            # Vérifier si un filtre et actif et si oui est-ce que c'est la DT visé
            if filter_dt is None or dt.code() == filter_dt:
                # Ajouter les CS de la DT qui intersect la géometrie 
                list_cs.extend([cs for cs in dt if cs.contains(geom, proj)])
        return list_cs
    
    def getMRCByIntersection(self, geom:QgsGeometry, proj:QgsCoordinateReferenceSystem=None)->list[MRC]:
        """ Méthode qui retourn une liste des MRC qui intersectes avec la géométrie rentrée """
        return [mrc for mrc in self.dict_mrc.values() if mrc.contains(geom, proj)]
    
    def getMunByIntersection(self, geom:QgsGeometry, proj:QgsCoordinateReferenceSystem=None)->list[Municipalite]:
        """ Méthode qui retourn une liste des CS qui intersectes avec la géométrie rentrée """
        # Liste des objet Municipalite
        list_mun = []
        # Parcourir la liste des Municipalité qui intersect la géometrie
        for cs in self.getCSByIntersection(geom, proj):
            # Ajouter les Municipalité qui intersect la géometrie 
            list_mun.extend([mun for mun in cs if mun.contains(geom, proj)])
        return list_mun
        
    def getCS(self, value, dt:Union[DT, str, int]=None):
        """ Permet de retourner l'objet CS selon un code ou un nom """
        if dt is None: list_dt = self.getListDT()
        else: list_dt = [self.getDT(dt)]
        for dt in list_dt:
            cs = dt.getCS(value)
            if cs is not None: return cs
        return None
    
    def getDT(self, value)->DT:
        """ Permet de retourner l'objet DT selon un code ou un nom ou un objet DT """
        if isinstance(value, DT): value = value.code()
        for dt in self:
            if dt == value: return dt
        return None

    def getMRC(self, value)->MRC:
        """ Permet de retourner l'objet MRC selon un code ou un nom ou un objet MRC """
        if isinstance(value, MRC): value = value.code()
        for mrc in self.dict_mrc.values():
            if mrc == value: return mrc
        return None

    def getListCodeDT(self):
        """ Méthode qui permet de retourner une liste des codes de DT de la Province """
        return list(self.dict_dt.keys())
    
    def getListCodeMRC(self):
        """ Méthode qui permet de retourner une liste des codes de MRC de la Province """
        return list(self.dict_mrc.keys())
    
    def getListDT(self)-> list[DT]: 
        """ Méthode qui permet de retourner une liste des objet DT de la Province """
        return list(self.dict_dt.values())
    
    def getListMRC(self)-> list[MRC]: 
        """ Méthode qui permet de retourner une liste des objet MRC de la Province """
        return list(self.dict_mrc.values())
        
    def getListNameDT(self, type="court"):
        """ Retourne une list des noms des dt présents dans la province """
        return [dt.name(type=type) for dt in self.getListDT()]
    
    def getListNameMRC(self):
        """ Retourne une list des noms des MRC présents dans la province """
        return [mrc.name() for mrc in self.getListMRC()]


