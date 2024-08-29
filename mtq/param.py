# -*- coding: utf-8 -*-

# ======================== Nom des options par défault ============================
# Nom de la couche des RTSS 
DEFAULT_NOM_COUCHE_RTSS = "BGR - RTSS"
# Nom du champ qui contient les RTSS 
DEFAULT_NOM_CHAMP_RTSS = "num_rts"
# Nom du champ qui contient le chainage de début (None pour vas donnée toute le temps une valeur de 0)
DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE = None
# Nom du champ qui contient le chainage de fin 
DEFAULT_NOM_CHAMP_FIN_CHAINAGE = "val_longr_sous_route"

# Chemin vers le Excel contenant les couches vectorielle de base
DEFAULT_LAYER_REFERENCE = "//Mtq.min.intra/fic/ESTRIE/Espace Collaboratif/Cartographie/Profils SIG/QGIS/Référence des couches.xlsx"
# L'indentifiant de l'authentification des services web QGIS
DEFAULT_AUTHID = "9mtq103"

# name = Nom de la couche (doit être unique)
C_NAME = "name"
# alias = Nom qui apparait dans la recherche
C_ALIAS = "alias"
# tag = Liste de mots clé séparé par des ; pour la recherche
C_TAG = "tag"
# source = Le chemin pour se rendre à la couche
C_SOURCE = "source"
# provider = Le type de couche
C_PROV = "provider"
# key_fields = Le nom du champs qui sert d'identifiant
C_ID_NAME = "key_fields"
# key_fields_type = Le type du champs qui sert d'identifiant
C_ID_TYPE = "key_fields_type"
# code_dt_field = Le nom du champs qui contient un code (format text) de DT 
C_DT = "code_dt_field"
# type_code_dt_field = La réprensentation de l'identifiant de la DT. Les valeurs possibles sont (code, court, long, complet)
C_TYPE_DT = "type_code_dt_field"
# code_cs_field = Le nom du champs qui contient un code (format text) de CS
C_CS = "code_cs_field"
# type_code_cs_field = La réprensentation de l'identifiant du CS. Les valeurs possibles sont (code, court, long, complet)
C_TYPE_CS = "type_code_cs_field"
# recherche = La liste des champs à utiliser pour la recherche dans la couche (text séparéer par des ";")
C_SEARCH_FIELDS = "recherche"
# requests = Un dictionnaire des requetes de la couche
C_REQUESTS = "requests"
# styles = Un dictionnaire des styles de la couche
C_STYLES = "styles"
# default_style = Le style par défault de la couche
C_DEFAULT_STYLE = "default_style"
# description = Une courte description de la couche
C_DESCRIPTION = "description"
# geocatalogue = Le lien vers la fiche du géocatalogue
C_GEOCATALOGUE = "geocatalogue"

# Nom de la couche des Municipalité
DEFAULT_NOM_COUCHE_MUN = 'Municipalité'
# Nom du champ qui contient les codes de Municipalité
DEFAULT_NOM_CHAMP_CODE_MUN = 'mus_co_geo'
# Nom du champ qui contient les noms de Municipalité
DEFAULT_NOM_CHAMP_NOM_MUN = 'mus_nm_mun'
# Nom du champ qui contient les codes de MRC dans les Municipalité
DEFAULT_NOM_CHAMP_MUN_CODE_MRC = 'mus_co_mrc'

# Nom de la couche des MRC
DEFAULT_NOM_COUCHE_MRC = 'Municipalité régionale de comptée (MRC)'
# Nom du champ qui contient les codes de MRC
DEFAULT_NOM_CHAMP_CODE_MRC = 'mrs_co_mrc'
# Nom du champ qui contient les noms de MRC
DEFAULT_NOM_CHAMP_NOM_MRC = 'mrs_nm_mrc'

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

# Nom du champs de l'identifiant dans l'index du lidar mobile
DEFAULT_NOM_CHAMP_LIDAR_ID = "id_index"
# Nom du champs de la date dans l'index du lidar mobile
DEFAULT_NOM_CHAMP_LIDAR_DATE = "date"
# Nom du champs du lien de téléchargement dans l'index du lidar mobile
DEFAULT_NOM_CHAMP_LIDAR_TELECHARGEMENT = "fichier1_u"

# Dictionnaire contenant toute les DT et toute les CS pour la creation d'une Province
DICT_PROVINCE:dict[str, dict[str, dict[str, str]]] = {
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
