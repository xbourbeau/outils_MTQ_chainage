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

""" Object représentant une région administrative """
class Region:

    def __init__(self, code, name, geom=None, proj=None):
        # Définir les pramètres de l'oject région
        self.setCode(code)
        self.setName(name)
        self.setGeometry(geom, proj)

    # Méthode qui retourne le code de la région
    def getCode(self):
        return self.code

    # Méthode qui retourne le nom de la région
    def getName(self):
        return self.name

    # Méthode qui retourne la géométrie de la région
    def getGeom(self):
        return self.geom

    # Méthode qui permet de vérifie si une géométrie est dans la région
    def contains (self, geom_to_check, proj):
        # Reprojecter la geometrie dans le même système de coordonnées si 2 projection sont défini
        if self.proj and proj: geom_to_check = reprojectGeometry(geom_to_check, proj, self.proj)
        
        # Retrouner VRAI ou FAUX selon l'intersection
        if self.geom.boundingBoxIntersects(geom_to_check): return self.geom.intersects(geom_to_check)
        return False

    # Méthode pour définir le code de la région
    def setCode(self, code):
        self.code = int(code)

    # Méthode pour définir le nom de la région
    def setName(self, name):
        self.name = name

    # Méthode pour définir une geometry et un projection pour la région
    def setGeometry(self, geom, proj=None):
        self.geom = geom
        self.proj = proj


""" Object représentant les centres de services du MTQ """
class CS(Region):
    def __init__(self, code, name, geom=None, proj=None):
        Region.__init__(self, code, name, geom, proj)
        # List des préfix possible pour le nom du CS
        self.prefix = ("CS des ", "CS de ", "CS d' ")
    
    # Méthode qui retourne le nom du CS
    def getName(self, complet=False):
        # Retroune le nom complet avec préfix
        if complet: return self.name
        # Retire le préfix du nom
        else:
            name = self.name
            for s in self.prefix: name = name.replace(s, '')
            return name

""" Object représentant les directions territoriale du MTQ """
class DT (Region):
    
    def __init__(self, code, name, geom=None, proj=None):
        Region.__init__(self, code, name, geom, proj)
        # Définir les pramètres de l'oject DT
        self.dict_cs = {}
        # List des préfix possible pour le nom de la DT
        self.prefix = ("DG de l'", "DG de la ", "DG du ", "DG des ", "DG d'")
    
    # Méthode qui permet d'ajouter un objet Region a l'interieur de la DT
    def addCS(self, cs):
        if cs.getCode() in self.dict_cs: return False
        self.dict_cs[cs.getCode()] = cs
        return True

    # Méthode qui permet de retourner le CS selon un code
    def getCS(self, code_cs):
        if code_cs in self.dict_cs: return self.dict_cs[code_cs]
        else: return None

    # Méthode qui permet de retourner une liste des codes de CS de la DT
    def getListCodeCS(self):
        return list(self.dict_cs.keys())
    
    # Méthode qui permet de retourner une liste des objet CS de la DT
    def getListCS(self):
        return self.dict_cs.values()

    # Retourne une list des noms des cs présents dans le dt
    def getListNameCS(self, complet=False):
        return [cs.getName(complet) for cs in self.getListCS()]

    # Méthode qui retourne le nom du CS
    def getName(self, complet=False):
        # Retroune le nom complet avec préfix
        if complet: return self.name
        # Retire le préfix du nom
        else:
            name = self.name
            for s in self.prefix: name = name.replace(s, '')
            return name
        
    # Permet de vérifier si un un CS est dans une DT
    def isInDT(self, value):
        for code_cs,  cs in self.dict_cs.items():
            # Vérifier si la valeur est un chiffre
            if isinstance(value, int):
                if code_cs == value: return True
            # Vérifier si la valeur est un texte
            elif isinstance (value, str):
                if cs.getName(True) == value or cs.getName(False) == value: return True
            # Vérifier si la valeur est un objet CS
            elif isinstance (value, CS):
                if code_cs == value.getCode(): return True  
        return False


""" Object représentant la province du Québec """
class Province(Region):
    
    def __init__(self, code, name, geom=None, proj=None): 
        Region.__init__(self, code, name, geom, proj)
        # Définir les pramètres de l'oject DT
        self.dict_dt = {}
    
    ''' Constructeur des CS et DT dans l'objet Province a partir des couches '''
    @classmethod
    def fromLayer(cls,
                  layer_dt,
                  layer_cs,
                  champ_code_dt=DEFAULT_NOM_CHAMP_CODE_DT,
                  champ_nom_dt=DEFAULT_NOM_CHAMP_NOM_DT,
                  champ_code_cs=DEFAULT_NOM_CHAMP_CODE_CS,
                  champ_nom_cs=DEFAULT_NOM_CHAMP_NOM_CS,
                  champ_cs_code_DT=DEFAULT_NOM_CHAMP_CS_CODE_DT):
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
    

    ''' Constructeur des CS et DT dans l'objet Province a partir du projet '''
    @classmethod
    def fromMemory(cls):
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

    ''' Constructeur des CS et DT dans l'objet Province a partir du projet '''
    @classmethod
    def fromProject(cls,
                  layer_dt_name=DEFAULT_NOM_COUCHE_DT,
                  layer_cs_name=DEFAULT_NOM_COUCHE_CS,
                  champ_code_dt=DEFAULT_NOM_CHAMP_CODE_DT,
                  champ_nom_dt=DEFAULT_NOM_CHAMP_NOM_DT,
                  champ_code_cs=DEFAULT_NOM_CHAMP_CODE_CS,
                  champ_nom_cs=DEFAULT_NOM_CHAMP_NOM_CS,
                  champ_cs_code_DT=DEFAULT_NOM_CHAMP_CS_CODE_DT):
        # Définir et la couche des DT dans le projet
        layer_dt = validateLayer(layer_dt_name, [champ_code_dt, champ_nom_dt], geom_type=2)
        # Définir et la couche des CS dans le projet
        layer_cs = validateLayer(layer_cs_name, [champ_code_cs, champ_nom_cs, champ_cs_code_DT], geom_type=2)
        # Créer un objet Province avec les couches s'il sont valide
        if layer_dt and layer_cs: return cls.fromLayer(layer_dt, layer_cs, champ_code_dt, champ_nom_dt, champ_code_cs, champ_nom_cs, champ_cs_code_DT)
        # Sinon retourner un objet Province vide
        return cls(53, "QuébecEmpty")

    # Méthode qui retourn une liste des DT qui intersectes avec la géométrie rentrée
    def DTIntersection(self, geom, proj=None):
        return [dt for dt in self.dict_dt.values() if dt.contains(geom, proj)]

    # Méthode qui retourn une liste des CS qui intersectes avec la géométrie rentrée
    def CSIntersection(self, geom, proj=None, filter_dt=None):
        # Liste des objet CS
        list_cs = []
        # Parcourir la liste des DT qui intersect la géometrie
        for dt in self.DTIntersection(geom, proj):
            # Vérifier si un filtre et actif et si oui est-ce que c'est la DT visé
            if filter_dt is None or dt.getCode() == filter_dt:
                # Ajouter les CS de la DT qui intersect la géometrie 
                list_cs += [cs for cs in dt.getListCS() if cs.contains(geom, proj)]
        return list_cs
        

    # Méthode qui permet d'ajouter un objet Region a l'interieur de la Province
    def addDT(self, dt):
        if dt.getCode() in self.dict_dt: return False
        self.dict_dt[dt.getCode()] = dt
        return True
    
    # Méthode qui permet de retourner la DT selon un code
    def getDT(self, code_dt):
        if code_dt in self.dict_dt: return self.dict_dt[code_dt]
        else: return None

    # Méthode qui permet de retourner la DT selon un nom
    def getDTByName(self, name_dt):
        for dt in self.getListDT():
            if dt.getName(True) == name_dt or dt.getName(False) == name_dt: return dt
        return None

    # Méthode qui permet de retourner une liste des codes de DT de la Province
    def getListCodeDT(self):
        return list(self.dict_dt.keys())

    # Méthode qui permet de retourner une liste des objet DT de la Province
    def getListDT(self):
        return self.dict_dt.values()
        
    #Retourne une list des noms des dt présents dans la province
    def getListNameDT(self, complet=False):
        return [dt.getName(complet) for dt in self.getListDT()]

    # Permet de vérifier si une DT est dans la Province
    def isInDT(self, value):
        for code_dt,  dt in self.dict_dt.items():
            # Vérifier si la valeur est un chiffre
            if isinstance(value, int):
                if code_dt == value: return True
            # Vérifier si la valeur est un texte
            elif isinstance (value, str):
                if dt.getName(True) == value or dt.getName(False) == value: return True
            # Vérifier si la valeur est un objet DT
            elif isinstance (value, DT):
                if code_dt == value.getCode(): return True  
        return False
        
pass