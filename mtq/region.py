# -*- coding: utf-8 -*-
from .fnt import reprojectGeometry, validateLayer

# ======================== Nom des options par défault ============================
# Nom de la couche des CS 
DEFAULT_NOM_COUCHE_CS = 'Centre de services - MTQ'
# Nom du champ qui contient les codes de CS
DEFAULT_NOM_CHAMP_CODE_CS = 'cod_niv_hierc_3'
# Nom du champ qui contient les noms de CS
DEFAULT_NOM_CHAMP_NOM_CS = 'nom_unite_admns_court'
# Nom du champ qui contient les codes de DT dans les CS
DEFAULT_NOM_CHAMP_CS_CODE_DT = 'cod_niv_hierc_2'

# Nom de la couche des DT 
DEFAULT_NOM_COUCHE_DT = 'Direction générale territoriale - MTQ'
# Nom du champ qui contient les codes de CS
DEFAULT_NOM_CHAMP_CODE_DT = 'cod_niv_hierc_2'
# Nom du champ qui contient les noms de CS
DEFAULT_NOM_CHAMP_NOM_DT = 'nom_unite_admns_court'

# Dictionnaire contenant toute les DT et toute les CS pour la creation d'une Province
DICT_PROVINCE = {
    '81': {'DT': "DG des projets et de l'exploitation aéroportuaire",
        'CS':{
            '02':"Aéroports nordiques",
        }
    },
    '29': {'DT': "DG de l'exploitation du réseau métropolitain",
        'CS':{
            '02':"Dir. du soutien à l'entretien courant",
        }
    },
    '93': {'DT': "DG d'Eeyou Istchee Baie-James",
        'CS':{
            '04':"CS de Chibougamau",
        }
    },
    '68': {'DT': "DG du Saguenay - Lac-Saint-Jean",
        'CS':{
            '06':"CS de Chicoutimi",
            '07':"CS d'Alma",
            '08':"CS de Roberval",
        }
    },
    '66': {'DT': "DG de la Chaudière-Appalaches",
        'CS':{
            '07':"CS de Thetford Mines",
            '11':"CS de Lac-Etchemin",
            '08':"CS de Saint-Jean-Port-Joli",
            '10':"CS de Lévis",
            '06':"CS de Beauceville",
            '09':"CS de Saint-Michel-de-Bellechasse",
        }
    },
    '71': {'DT': "DG de la Capitale-Nationale",
        'CS':{
            '86':"CS de Cap-Santé",
            '85':"CS de La Malbaie",
            '84':"CS de Québec",
        }
    },
    '64': {'DT': "DG du Centre-du-Québec",
        'CS':{
            '06':"CS de Nicolet",
            '07':"CS de Victoriaville",
            '08':"CS de Drummondville",
        }
    },
    '70': {'DT': "DG de la Mauricie",
        'CS':{
            '06':"CS de Shawinigan",
            '07':"CS de Trois-Rivières",
        }
    },
    '63': {'DT': "DG de la Gaspésie - Îles-de-la-Madeleine",
        'CS':{
            '07':"CS de Gaspé",
            '08':"CS de Sainte-Anne-des-Monts",
            '06':"CS des Îles-de-la-Madeleine",
            '09':"CS de New Carlisle",
        }
    },
    '65': {'DT': "DG du Bas-Saint-Laurent",
        'CS':{
            '07':"CS de Témiscouata-sur-le-Lac",
            '09':"CS de Saint-Pascal",
            '08':"CS de Cacouna",
            '06':"CS de Mont-Joli",
        }
    },
    '67': {'DT': "DG de la Côte-Nord",
        'CS':{
            '09':"CS de Bergeronnes",
            '07':"CS de Sept-Îles",
            '08':"CS de Baie-Comeau",
            '06':"CS de Havre-Saint-Pierre",
        }
    },
    '86': {'DT': "DG de la Montérégie",
        'CS':{
            '12':"CS d'Ormstown",
            '13':"CS de Napierville",
            '11':"CS de Saint-Jean-sur-Richelieu",
            '10':"CS de Saint-Hyacinthe",
        }
    },
    '88': {'DT': "DG des Laurentides - Lanaudière",
        'CS':{
            '07':"CS de Saint-Jérôme",
            '06':"CS de Joliette",
            '09':"CS de Mont-Laurier",
        }
    },
    '89': {'DT': "DG de l'Outaouais",
        'CS':{
            '08':"CS de Campbell's Bay",
            '06':"CS de Papineauville",
            '07':"CS de Gatineau",
            '09':"CS de Maniwaki",
        }
    },
    '91': {'DT': "DG de l'Abitibi-Témiscamingue",
        'CS':{
            '10':"CS de Ville-Marie",
            '07':"CS de Rouyn-Noranda",
            '06':"CS de Val-d'Or",
            '08':"CS d'Amos",
            '09':"CS de Macamic",
        }
    },
    '90': {'DT': "DG de l'Estrie",
        'CS':{
            '10':"CS de Magog",
            '06':"CS de Lac-Mégantic",
            '07':"CS de Cookshire",
            '08':"CS de Sherbrooke",
            '12':"CS de Foster",
            '09':"CS de Richmond",
        }
    },
}

class Region:
    """ Object représentant une région administrative """
    def __init__(self, code, name, geom=None, proj=None):
        # Définir les pramètres de l'oject région
        self.setCode(code)
        self.setName(name)
        self.setGeometry(geom, proj)

    def getCode(self, as_string=False):
        """ Méthode qui retourne le code de la région """
        if as_string:
            if self.code < 10: return '0'+ str(self.code)
            else: return str(self.code)
        return self.code

    def getName(self):
        """ Méthode qui retourne le nom de la région """
        return self.name

    def getGeom(self):
        """ Méthode qui retourne la géométrie de la région """
        return self.geom
    
    def contains (self, geom_to_check, proj):
        """ Méthode qui permet de vérifie si une géométrie est dans la région """
        # Reprojecter la geometrie dans le même système de coordonnées si 2 projection sont défini
        if self.proj and proj: geom_to_check = reprojectGeometry(geom_to_check, proj, self.proj)
        # Retrouner VRAI ou FAUX selon l'intersection
        if self.geom.boundingBoxIntersects(geom_to_check): return self.geom.intersects(geom_to_check)
        return False

    def setCode(self, code):
        """ Méthode pour définir le code de la région """
        self.code = int(code)

    def setName(self, name):
        """ Méthode pour définir le nom de la région """
        self.name = name

    def setGeometry(self, geom, proj=None):
        """ Méthode pour définir une geometry et un projection pour la région """
        self.geom = geom
        self.proj = proj

class CS(Region):
    """ Object représentant les centres de services du MTQ """
    def __init__(self, code, name, geom=None, proj=None):
        Region.__init__(self, code, name, geom, proj)
        # List des préfix possible pour le nom du CS
        self.prefix = ("CS des ", "CS de ", "CS d' ")
    
    # Méthode qui retourne le nom du CS
    def getName(self, type="court"):
        # Retroune le nom complet avec préfix
        if type == "complet": return self.name.replace("CS", 'Centre de services')
        elif type == "long": return self.name
        # Retire le préfix du nom
        else:
            name = self.name
            for s in self.prefix: name = name.replace(s, '')
            return name

class DT (Region):
    """ Object représentant les directions territoriale du MTQ """
    def __init__(self, code, name, geom=None, proj=None):
        Region.__init__(self, code, name, geom, proj)
        # Définir les pramètres de l'oject DT
        self.dict_cs = {}
        # List des préfix possible pour le nom de la DT
        self.prefix = ("DG de l'", "DG de la ", "DG du ", "DG des ", "DG d'")
    
    def addCS(self, cs):
        """ Méthode qui permet d'ajouter un objet Region a l'interieur de la DT """
        if cs.getCode() in self.dict_cs: return False
        self.dict_cs[cs.getCode()] = cs
        return True
    
    def getCS(self, value):
        """ Permet de retourner l'objet CS selon un code ou un nom """
        cs = None
        # Vérifier si la valeur est un chiffre
        if isinstance(value, int): cs = self.getCSByCode(value)
        # Vérifier si la valeur est un texte
        elif isinstance (value, str):
            cs = self.getCSByName(value)
            if cs is None: cs = self.getCSByCode(value)
        return cs
    
    def getCSByCode(self, code_cs):
        """ Méthode qui permet de retourner le CS selon un code """
        try:
            code_cs = int(code_cs)
            if code_cs in self.dict_cs: return self.dict_cs[code_cs]
            else: return None
        except: return None

    def getCSByName(self, name_cs):
        """ Méthode qui permet de retourner le CS selon un nom """
        for cs in self.getListCS():
            for type in ["court", "long", "complet"]:
                if cs.getName(type=type) == name_cs: return cs
        return None

    def getListCodeCS(self):
        """ Méthode qui permet de retourner une liste des codes de CS de la DT """
        return list(self.dict_cs.keys())
    
    def getListCS(self):
        """ Méthode qui permet de retourner une liste des objet CS de la DT """
        return self.dict_cs.values()

    def getListNameCS(self, type="court"):
        """ Retourne une list des noms des cs présents dans le dt """
        return [cs.getName(type=type) for cs in self.getListCS()]

    def getName(self, type="court"):
        """ Méthode qui retourne le nom du CS """
        # Retroune le nom complet avec préfix
        if type == "complet": return self.name.replace("DG", 'Direction générale')
        elif type == "long": return self.name
        # Retire le préfix du nom
        else:
            name = self.name
            for s in self.prefix: name = name.replace(s, '')
            return name
        
    def isInDT(self, value):
        """ Permet de vérifier si un un CS est dans une DT """
        for code_cs,  cs in self.dict_cs.items():
            # Vérifier si la valeur est un chiffre
            if isinstance(value, int):
                if code_cs == value: return True
            # Vérifier si la valeur est un texte
            elif isinstance (value, str):
                if self.getCSByName(value) is not None: return True
                elif self.getCS(value) is not None: return True
            # Vérifier si la valeur est un objet CS
            elif isinstance (value, CS):
                if code_cs == value.getCode(): return True  
        return False

class Province(Region):
    """ Object représentant la province du Québec """
    def __init__(self, code, name, geom=None, proj=None): 
        Region.__init__(self, code, name, geom, proj)
        # Définir les pramètres de l'oject DT
        self.dict_dt = {}
    
    @classmethod
    def fromLayer(cls,
                  layer_dt,
                  layer_cs,
                  champ_code_dt=DEFAULT_NOM_CHAMP_CODE_DT,
                  champ_nom_dt=DEFAULT_NOM_CHAMP_NOM_DT,
                  champ_code_cs=DEFAULT_NOM_CHAMP_CODE_CS,
                  champ_nom_cs=DEFAULT_NOM_CHAMP_NOM_CS,
                  champ_cs_code_DT=DEFAULT_NOM_CHAMP_CS_CODE_DT):
        """ Constructeur des CS et DT dans l'objet Province a partir des couches """
        # Créer un objet Province
        prov = cls(53, "Québec")
        dt_epsg = layer_dt.crs().authid().split(":")[1]
        cs_epsg = layer_cs.crs().authid().split(":")[1]
        # Parcourir les features DT de la couche
        for feat_dt in layer_dt.getFeatures():
            # Ajouter la DT à la Province
            prov.addDT(DT(feat_dt[champ_code_dt], feat_dt[champ_nom_dt], feat_dt.geometry(), dt_epsg))
        # Parcourir les features CS de la couche
        for feat_cs in layer_cs.getFeatures():
            # Définir la DT du CS
            dt = prov.getDT(feat_cs[champ_cs_code_DT])
            # Ajouter le CS à la DT de la Province si la DT à été ajouté
            if dt: dt.addCS(CS(feat_cs[champ_code_cs], feat_cs[champ_nom_cs], feat_cs.geometry(), cs_epsg))
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
            for code_cs, nom_cs in dt["CS"].items():
                obj_dt.addCS(CS(code_cs, nom_cs))
            # Ajouter la DT à la Province
            prov.addDT(obj_dt)
        return prov

    @classmethod
    def fromProject(cls,
                  layer_dt_name=DEFAULT_NOM_COUCHE_DT,
                  layer_cs_name=DEFAULT_NOM_COUCHE_CS,
                  champ_code_dt=DEFAULT_NOM_CHAMP_CODE_DT,
                  champ_nom_dt=DEFAULT_NOM_CHAMP_NOM_DT,
                  champ_code_cs=DEFAULT_NOM_CHAMP_CODE_CS,
                  champ_nom_cs=DEFAULT_NOM_CHAMP_NOM_CS,
                  champ_cs_code_DT=DEFAULT_NOM_CHAMP_CS_CODE_DT):
        """ Constructeur des CS et DT dans l'objet Province a partir du projet """
        # Définir et la couche des DT dans le projet
        layer_dt = validateLayer(layer_dt_name, [champ_code_dt, champ_nom_dt], geom_type=2)
        # Définir et la couche des CS dans le projet
        layer_cs = validateLayer(layer_cs_name, [champ_code_cs, champ_nom_cs, champ_cs_code_DT], geom_type=2)
        # Créer un objet Province avec les couches s'il sont valide
        if layer_dt and layer_cs: return cls.fromLayer(layer_dt, layer_cs, champ_code_dt, champ_nom_dt, champ_code_cs, champ_nom_cs, champ_cs_code_DT)
        # Sinon retourner un objet Province vide
        return cls(53, "QuébecEmpty")

    def DTIntersection(self, geom, proj=None):
        """ Méthode qui retourn une liste des DT qui intersectes avec la géométrie rentrée """
        return [dt for dt in self.dict_dt.values() if dt.contains(geom, proj)]
    
    def CSIntersection(self, geom, proj=None, filter_dt=None):
        """ Méthode qui retourn une liste des CS qui intersectes avec la géométrie rentrée """
        # Liste des objet CS
        list_cs = []
        # Parcourir la liste des DT qui intersect la géometrie
        for dt in self.DTIntersection(geom, proj):
            # Vérifier si un filtre et actif et si oui est-ce que c'est la DT visé
            if filter_dt is None or dt.getCode() == filter_dt:
                # Ajouter les CS de la DT qui intersect la géometrie 
                list_cs += [cs for cs in dt.getListCS() if cs.contains(geom, proj)]
        return list_cs
        
    def addDT(self, dt):
        """ Méthode qui permet d'ajouter un objet Region a l'interieur de la Province """
        if dt.getCode() in self.dict_dt: return False
        self.dict_dt[dt.getCode()] = dt
        return True
    
    def getCS(self, value):
        """ Permet de retourner l'objet CS selon un code ou un nom """
        cs = None
        for dt in self.getListDT():
            cs = dt.getCS(value)
            if cs is not None: break
        return cs
    
    def getDT(self, value):
        """ Permet de retourner l'objet DT selon un code ou un nom """
        dt = None
        # Vérifier si la valeur est un chiffre
        if isinstance(value, int):
            dt = self.getDTByCode(value)
        # Vérifier si la valeur est un texte
        elif isinstance (value, str):
            dt = self.getDTByName(value)
            if dt is None: dt = self.getDTByCode(value)
        return dt
    
    def getDTByCode(self, code_dt):
        """ Méthode qui permet de retourner la DT selon un code """
        try:
            code_dt = int(code_dt)
            if int(code_dt) in self.dict_dt: return self.dict_dt[code_dt]
            else: return None
        except: return None
    
    def getCSByName(self, name_cs):
        """ Méthode qui permet de retourner le CS selon un code """
        for dt in self.getListDT():
            cs = dt.getCSByName(name_cs)
            if cs: return cs
        return None
    
    def getDTByName(self, name_dt):
        """ Méthode qui permet de retourner la DT selon un nom """
        for dt in self.getListDT():
            for type in ["court", "long", "complet"]:
                if dt.getName(type=type) == name_dt: return dt
        return None

    def getListCodeDT(self):
        """ Méthode qui permet de retourner une liste des codes de DT de la Province """
        return list(self.dict_dt.keys())
    
    def getListDT(self):
        """ Méthode qui permet de retourner une liste des objet DT de la Province """
        return self.dict_dt.values()
        
    def getListNameDT(self, type="court"):
        """ Retourne une list des noms des dt présents dans la province """
        return [dt.getName(type=type) for dt in self.getListDT()]

    def isInProvince(self, value):
        """ Permet de vérifier si une DT est dans la Province """
        # Vérifier si la valeur est un chiffre
        if isinstance(value, int):
            if self.getDTByCode(value) is not None: return True
        # Vérifier si la valeur est un texte
        elif isinstance (value, str):
            if self.getDTByName(value) is not None: return True
            elif self.getDT(value) is not None: return True
        # Vérifier si la valeur est un objet DT
        elif isinstance (value, DT):
            if value.getCode() in self.getListCodeDT(): return True  
        else: return False
        
pass