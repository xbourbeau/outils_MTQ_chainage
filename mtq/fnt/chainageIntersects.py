# -*- coding: utf-8 -*-

import numpy as np

def chainageIntersects(c_compare, c_source):
    """
    Fonction compare deux liste de chainage de la même longueur pour savoir si les chainage s'intersect.
    Args:
        c_compare (liste): Liste des chainages #1
        c_source (liste): Liste des chainages #2

    Sortie:
        - (bool) = Si il y a une intersection
    """
    compare = np.append(np.array(c_compare), np.flip(np.array(c_compare)))
    source = np.append(np.array(c_source), np.array(c_source))
    if compare.size == source.size:
        lesser = np.less_equal(source, compare)
        greater = np.greater_equal(source, compare)
        return not (np.all(lesser) is np.any(lesser) and np.all(greater) is np.any(greater))   
    return None