# -*- coding: utf-8 -*-
from math import modf
from qgis.core import QgsGeometry, QgsPointXY

def verifyFormatPoint(point):
    """
    Fonction qui permet de toujours renvoyer une geometry (QgsGeometry).
    Renvoie un QgsGeometry si un point XY (QgsPointXY) est donnée

    Args:
        - point (QgsPointXY/QgsGeometry): Le point à vérifier
    """
    if isinstance(point, QgsPointXY): return QgsGeometry().fromPointXY(point)
    else: return point

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









