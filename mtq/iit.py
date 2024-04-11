# -*- coding: utf-8 -*-
def getMRCByCode(code):
    if str(code) == '30':
        return "Le Granit"
    elif str(code) == '40':
        return "Les Sources"
    elif str(code) == '41':
        return "Le Haut-Saint-François"
    elif str(code) == '42':
        return "Le Val-Saint-François"
    elif str(code) == '43':
        return "Sherbrooke"
    elif str(code) == '44':
        return "Coaticook"
    elif str(code) == '45':
        return "Memphrémagog"
    elif str(code) == '46':
        return "Brome-Missisquoi"
    elif str(code) == '47':
        return "La Haute-Yamaska"
    else: return None

def getCEPByCode(code):
    if str(code) == '104':
        return "Mégantic"
    elif str(code) == '110':
        return "Saint-François"
    elif str(code) == '116':
        return "Sherbrooke"
    elif str(code) == '120':
        return "Orford"
    elif str(code) == '126':
        return "Johnson"
    elif str(code) == '132':
        return "Richmond"
    elif str(code) == '204':
        return "Brome-Missisquoi"
    elif str(code) == '206':
        return "Granby"
    elif str(code) == '802':
        return "Beauce-Sud"
    else: return None
    
def getCodeTypeLigne(type_ligne):
    if type_ligne == 'Simple discontinue':
        return '01'
    elif type_ligne == 'Simple continue':
        return '02'
    elif type_ligne == u'Double discontinue à droite':
        return '03'
    elif type_ligne == u'Double discontinue à gauche':
        return '04'
    elif type_ligne == 'Double continue':
        return '05'
    elif type_ligne == 'Double discontinue':
        return '06'
    else:
        return ''
        
def getCodeCouleur(couleur):
    if couleur == 'Blanc':
        return '01'
    elif couleur == 'Jaune':
        return '02'
    elif couleur == 'Rouge':
        return '03'
    elif couleur == u'Blanc sur fond noir':
        return '05'
    else:
        return ''
        
def getCodeTypeMat(type_mat):
    if type_mat == u'Bandes préfabriquées':
        return '01'
    elif type_mat == 'MMA':
        return '22'
    elif type_mat == u"Produits expérimentaux":
        return '23'
    elif type_mat == u"Peinture à l'alkyde":
        return '45'
    elif type_mat == u"Peinture à l'époxy":
        return '46'
    elif type_mat == u"Peinture à l'eau":
        return '47'
    else:
        return '99'

def getCodeSousType(sous_type):
    if sous_type == u'Ligne axiale':
        return '01'
    elif sous_type == u'Ligne délimitation deux voies et plus même sens':
        return '02'
    elif sous_type == u'Ligne de délimitation de voie à circulation alternée':
        return '03'
    elif sous_type == u'Ligne délimitation voie réservée virage gauche deux sens':
        return '04'
    elif sous_type == u'Ligne délimitation voie réservée':
        return '05'
    elif sous_type == u'Ligne délimitation voie de dépassement':
        return '06'
    elif sous_type == u'Ligne délimitation voie véhicules lents':
        return '07'
    elif sous_type == u'Ligne de rive':
        return '08'
    elif sous_type == u'Ligne de continuité':
        return '09'
    elif sous_type == u'Ligne de guidage':
        return '10'
    elif sous_type == u"Ligne d'abord d'obstacles":
        return '11'
    elif sous_type == u"Ligne de céder le passage":
        return '12'
    else:
        return ''