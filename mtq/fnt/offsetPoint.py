# -*- coding: utf-8 -*-
from qgis.core import QgsPointXY
import math

def offsetPoint(point:QgsPointXY, offset, angle):
    """ 
    Fonction qui permet d'applique un offset perpendiculaire a un angle.

    Les delta X et delta Y sont de base calculer pour le cadrant Nord-Est avec l'angle du RTSS.
    Cependant, les delta reste les mêmes sauf pour le signe peut importe le cadrant
    si l'angle est (90, 180 ou 270) de plus. Le offset représente l'angle de la ligne + 90.
    Donc on applique les deltas pour le cadrant Sud-Est.

    Args:
        - point (QgsPointXY): Le point sur lequel appliquer un offset
        - offset (float/int): La distance du offset
        - angle (float/int): L'angle de la ligne pour avoir le offset perpendiculaire
    
    Return (QgsPointXY): Le point avec le offset appliquer.
    """
    # Coordonnée offset = coordonnée +/- delta
    x = point.x() + (math.cos(angle) * offset)
    y = point.y() - (math.sin(angle) * offset)
    return QgsPointXY(x, y)