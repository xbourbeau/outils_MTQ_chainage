# -*- coding: utf-8 -*-

import shapely.ops

def reverseGeom(geom:list):
    """
    Fonction qui inverse la géometrique d'un ligne

    Args:
        - geom (list coordonnée): La géometrie a inverser
    
    Return: La geometrie inversés
    """
    def _reverse(x, y, z=None):
        if z: return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]
    return shapely.ops.transform(_reverse, geom)