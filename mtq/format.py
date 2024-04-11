# -*- coding: utf-8 -*-
from math import modf
from qgis.core import (QgsGeometry, QgsPointXY)

def verifyFormatRTSS(rtss):
    if '-' in rtss: return deformaterRTSS(rtss)
    else: return rtss

def verifyFormatChainage(chainage):
    try:
        if '+' in str(chainage): return float(deformaterChainage(chainage))
        else: return float(chainage)
    except: return None

def verifyFormatPoint(point):
    if isinstance(point, QgsPointXY): return QgsGeometry().fromPointXY(point)
    else: return point
  
'''
Fonction qui convertie un chaînage numérique à un chaînage formater textuellement
# chaînage numérique --> chaînage formater
Format du chainage = 0+000.0
Entrée:
    - chainage (str/float/int) = Le chainage à convertir
    - precision (int) = Le nombre determinant la valeur pour à arrondire
'''

def formaterChainage (chainage, precision=None):
    # chaînage numérique --> chaînage formater
    # Déterminer la précision si elle n'est pas déterminé
    if precision is None: precision = [round(chainage, i) == round(chainage,3) for i in [0, 1, 2, 3]].index(True)
    
    # Determiner si le format est entier ou réel
    if precision <= 0: # Entier
        # Calculer le chainage arrondie selon la précision définie
        chainage = int(round(chainage, precision))
        # Format à appliquer pour un nombre entier
        number_format = '{:03}'
    else: # Réel
        # Format à appliquer pour un nombre réel avec la précision définie
        number_format = '{:0%i.%if}' % (4 + precision, precision)
    # Déterminer les milliers
    millier = int(chainage / 1000)
    # Formater le nombre selon le formatage définie 
    val_convertie = str(millier) + "+" + number_format.format(
                    chainage - (millier*1000))
    # Retourner la valeur formatée
    return val_convertie       

'''
Fonction qui convertie un chaînage formater vers un chaînage numérique
chaînage formater --> chaînage numérique
Format du chainage = 0+000.0
Entrée:
    - chainage (str/float/int) = Le chainage à convertir
    - precision (int) = Le nombre determinant la valeur pour à arrondire
'''
def deformaterChainage (chainage, precision=None):
    # chaînage formater --> chaînage numérique
    # Déterminer la précision si elle n'est pas déterminé
    if precision is None:
        if '.' in chainage: precision = len(chainage[chainage.find('.')+1:])
        else: precision = 0
    
    # Séparer les milliers et les centaines par le "+"
    millier, centaine = chainage.split('+')
    # Convertir les milliers et les centaines en nombre
    val_convertie = int(millier) *1000 + float(centaine)
    # Arrondir la valeur selon la précision définie
    val_convertie = round(val_convertie, precision)
    
    # Convertir en nombre entier si la précision est de 0 ou moins
    if precision <= 0: val_convertie = int(val_convertie)
    
    # Retourner la valeur formatée
    return val_convertie       

def formaterRTSS(rtss):
    # Numéro de la route
    route = rtss[:5]
    # Numéro du troncon
    tronc = rtss[5:7]
    # Numéro de la section
    sec = rtss[7:10]
    # Numéro de la sous-route
    sous_route = rtss[10:]
    # RTSS formater
    rtss_formater = '%s-%s-%s-%s' % (route, tronc, sec, sous_route)
    
    # Retourner le RTSS formater
    return rtss_formater   

def deformaterRTSS(rtss):
    rtss_formater = rtss.replace('-', '')
    
    # Retourner le RTSS formater
    return rtss_formater   

# Prend un numéro de projet et renvoie ça version formaté ex: 15402943 -> 154-02-943
def formaterProjet(num_projet, inverse=False):
    # Si le projet est déjà formater
    if inverse:
        # Retirer les tirets
        projet_formater = num_projet.replace('-', '')
    else:
        num_projet = str(num_projet)
        # Numéro de la route
        p1 = num_projet[:3]
        # Numéro du troncon
        p2 = num_projet[3:5]
        # Numéro de la section
        p3 = num_projet[5:]
        # RTSS formater
        projet_formater = '%s-%s-%s' % (p1, p2, p3)
    
    # Retourner le RTSS formater
    return projet_formater    

'''
    Convertie un angle de degres vers degres minute seconde
    
    Entrée:
        - deg(float/int) = L'angle en degres
        - type(str) = Indique le format
            (lat adds N or S à la fin)
            (lon adds E or W à la fin)
            (None garde le signe négatif)
'''
def degToDMS(deg, type=None, precision=0):
    decimals, number = modf(deg)
    d = int(number)
    m = int(decimals * 60)
    s = (deg - d - m / 60) * 3600.00
    
    compass = { 'lat': ('N','S'), 'lon': ('E','W')}
    dms_string = "{}º{:02d}'{:%i.%if}\"" % (precision+2, precision)
    if type in compass:
        dms_string += " {}"
        dms = dms_string.format(abs(d), abs(m), abs(s), compass[type][0 if d >= 0 else 1])
    else: dms = dms_string.format(d, abs(m), abs(s))
    return dms


    
pass









