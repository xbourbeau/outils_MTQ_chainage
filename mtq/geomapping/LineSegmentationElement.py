# -*- coding: utf-8 -*-
from typing import Dict
import copy

class LineSegmentationElement:
    """ Représente un Élément linéaire d'une segmentation """
    __slots__ = ("identifiant", "offset_d", "offset_f", "attributs", "intepolate_on_rtss")

    def __init__(self, id, offset_d=0, offset_f=None, attributs={}, intepolate_on_rtss=True):
        self.identifiant = id
        self.setOffsetDebut(offset_d)
        if offset_f is None: offset_f = offset_d
        self.setOffsetFin(offset_f)
        self.attributs = attributs
        self.intepolate_on_rtss = intepolate_on_rtss
    
    def __deepcopy__(self, memo):
        new_obj = self.__class__.__new__(self.__class__)

        # Add the new object to the memo dictionary to avoid infinite recursion
        memo[id(self)] = new_obj

        # Deep copy all the attributes
        for slot in self.__slots__:
            v = getattr(self, slot)
            setattr(new_obj, slot, copy.deepcopy(v, memo))

        return new_obj

    def getAttribut(self, name):
        """ Permet de retrourner une valeurs d'attribut de l'élément """
        return self.attributs.get(name, None)
    
    def getAttributs(self)->Dict:
        """ Permet de retrourner le dictionnaire des attributs de l'élément """
        return self.attributs
    
    def getAttributsName(self)->list:
        """ Permet de retrourner une liste des noms des attributs de l'élément """
        return list(self.attributs.keys())
    
    def getAttributsValues(self)->list:
        """ Permet de retrourner une liste des valeurs des attributs de l'élément """
        return list(self.attributs.values())

    def getOffsetDebut(self):
        """ Permet de retourner le offset de début """
        return self.offset_d
    
    def getOffsetFin(self):
        """ Permet de retourner le offset de fin """
        return self.offset_f

    def id(self):
        """ Permet de retourner l'identifiant de l'élément """
        return self.identifiant

    def isParallel(self):
        """ Permet de vérifier si l'élément est parallel au RTSS """
        return self.getOffsetDebut() == self.getOffsetFin()

    def setAttribut(self, name, value):
        """
        Permet de définir un attribut du RTSS.

        Args:
            - name (str): Le nom de l'attribut à définir
            - value (any): La valeur de l'attribut
        """
        self.attributs[name] = value

    def setId(self, id):
        self.identifiant = id

    def setInterpolation(self, intepolate:bool):
        """ Permet de définir la valeur d'interpolation """
        self.intepolate_on_rtss = intepolate

    def setOffsetDebut(self, offset):
        """ Permet de définir la valeur de offset de début """
        self.offset_d = offset

    def setOffsetFin(self, offset):
        """ Permet de définir la valeur de offset de fin """
        self.offset_f = offset