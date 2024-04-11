# -*- coding: utf-8 -*-
from math import modf
from qgis.core import QgsGeometry, QgsPointXY

def verifyFormatRTSS(rtss):
    """
    Fonction qui permet de toujours renvoyer un rtss non formater valide.

    Args:
        - point (str/int): Le rtss à vérifier
    """
    if not isinstance(rtss, str): rtss = str(rtss)
    if " " in rtss: rtss = rtss.replace(" ", "")
    if "-" in rtss: rtss = deformaterRTSS(rtss)
    if len(rtss) >= 11:  rtss = rtss.rjust(14, '0')
    return rtss

def verifyFormatChainage(chainage):
    """
    Fonction qui permet de toujours renvoyer un chainage numérique.

    Args:
        - chainage (numeric/str): Le chainage à vérifier
    """
    try:
        if ',' in str(chainage): chainage = chainage.replace(",", ".")
        if '+' in str(chainage): return float(deformaterChainage(chainage))
        else: return float(chainage)
    except: return None

def verifyFormatPoint(point):
    """
    Fonction qui permet de toujours renvoyer une geometry (QgsGeometry).
    Renvoie un QgsGeometry si un point XY (QgsPointXY) est donnée

    Args:
        - point (QgsPointXY/QgsGeometry): Le point à vérifier
    """
    if isinstance(point, QgsPointXY): return QgsGeometry().fromPointXY(point)
    else: return point
  
def formaterChainage(chainage, precision=None, inverse=False):
    """
    Fonction qui convertie un chaînage numérique à un chaînage formater textuellement
    Ex: chaînage numérique (0000.0) -> chaînage formater (0+000.0)

    Args:
        - chainage (str/numeric): Le chainage à convertir
        - precision (int): Le nombre determinant la valeur pour à arrondire
        - inverse (bool): True=[2+498 => 2498] False=[2498 => 2+498] 
    """
    # chaînage formater --> chaînage numérique
    if inverse:
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
    # chaînage numérique --> chaînage formater
    else:
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
        # Retourner le nombre selon le formatage définie 
        return str(millier) + "+" + number_format.format(chainage - (millier*1000))       

def deformaterChainage(chainage, precision=None):
    """
    Fonction qui convertie un chaînage formater à un chaînage numérique
    Ex: chaînage formater (0+000.0) -> chaînage numérique (0000.0)

    Args:
        - chainage (str/float/int): Le chainage à convertir
        - precision (int): Le nombre determinant la valeur pour à arrondire
    """
    return formaterChainage(chainage, precision, inverse=True)

def formaterRTSS(rtss, inverse=False):
    """
    Formater un numéro de RTSS avec des tirets.
    ex: 0001001210000C -> 00010-01-210-000C

    Args:
        - rtss (str): Le numéro de projet à formater
        - inverse (bool): True=[00010-01-210-000C => 0001001210000C] False=[0001001210000C => 00010-01-210-000C] 
    """
    if inverse: return rtss.replace('-', '')
    else: return f"{rtss[:5]}-{rtss[5:7]}-{rtss[7:10]}-{rtss[10:]}"

def deformaterRTSS(rtss):
    """
    Déformater un numéro de RTSS avec des tirets.
    ex: 00010-01-210-000C -> 0001001210000C

    Args:
        - rtss (str): Le numéro de projet à formater
    """
    return formaterRTSS(rtss, inverse=True)

def formaterProjet(num_projet, inverse=False):
    """
    Prend un numéro de projet et renvoie ça version formaté ex: 15402943 -> 154-02-943

    Args:
        - num_projet (str/int): Le numéro de projet à formater
        - inverse (bool): True=[154-02-943 => 15402943] False=[15402943 => 154-02-943] 
    """
    num_projet = str(num_projet)
    # Retourner le projet déformater
    if inverse: return num_projet.replace('-', '')
    # Retourner le projet formater
    else: return f"{num_projet[:3]}-{num_projet[3:5]}-{num_projet[5:]}"

def deformaterProjet(num_projet): 
    """
    Prend un numéro de projet et renvoie ça version déformaté ex: 154-02-943 -> 15402943 

    Args:
        - num_projet (str/int): Le numéro de projet à déformater
    """
    return formaterProjet(num_projet, inverse=True)

def degToDMS(deg, type="", precision=0):
    """
    Convertie un angle de degres vers degres minute seconde
    
    Args:
        - deg (float/int): L'angle en degres
        - type (str): Indique le format [lat: adds N or S à la fin], [lon: adds E or W à la fin], [empty: garde le signe négatif]
        - precision (int): la precision des secondes 
    """
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

def formaterLot(num_lot, inverse=False):
    """
    Permet de formater un numéro de lot avec des espaces.

    Args:
        - num_lot (int/str): Le numéro de lot
        - inverse (bool): True=[7 483 327 => 7483327] False=[7483327 => 7 483 327] 
    """
    num_lot = str(num_lot)
    # Retourner le lot formater
    if inverse: return int(num_lot.replace(" ", ""))
    else: return f"{num_lot[0]} {num_lot[1:4]} {num_lot[4:]}"
    
def deformaterLot(num_lot):
    """
    Permet de déformater un numéro de lot en retirant les espaces.

    Args:
        - num_lot (int/str): Le numéro de lot
    """
    return formaterLot(num_lot, inverse=True)









