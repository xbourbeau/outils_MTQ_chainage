# -*- coding: utf-8 -*-

def interpolateOffsetOnLine(dist, longeur, offset_d, offset_f):
    """
    Méthode qui permet de calculer le offset d'une ligne à un chainage par rapport au RTSS.

    Args:
        - dist (real): La distance le long de la longueur ou interpoler le offset
        - longeur (real): La longueur de la ligne entre les deux offsets
        - offset_d (real): Le offset de début de la ligne
        - offset_f (real): Le offset de fin de la ligne
    """
    # Différence du offset
    offset_diff = offset_f - offset_d
    # Retourner le offset de la ligne à la position du chainage
    return (((dist-0) * offset_diff)/longeur) + offset_d