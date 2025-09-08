# -*- coding: utf-8 -*-
from typing import Dict

import copy

class SegmentationElement:
    """ Représente l'élément d'une segmentation d'un RTSS """
    
    __slots__ = ("attributs", "intepolate_on_rtss")

    def __init__(self, **kwargs):
        """
        Construcuteur par défault d'un objet SegmentationElement.

        Args:
            - **kwargs: Les attributs de l'élément
        """
        self.attributs = {}
        # Set les attributs de l'élément 
        self.setAttributs(kwargs)
    
    def __str__(self): return f"Values: {self.getAttributs()}"
        
    def __repr__(self): return f"SegmentationElement {str(self)}"
    
    def __getitem__(self, index): return self.getAttribut(index)

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
        return 0
    
    def getOffsetFin(self):
        """ Permet de retourner le offset de fin """
        return 0

    def isParallel(self):
        """ Permet de vérifier si l'élément est parallel au RTSS """
        return self.getOffsetDebut() == self.getOffsetFin()
    
    def isOnRTSS(self):
        return self.isParallel() and self.getOffsetDebut() == 0
    
    def isEmpty(self):
        """ Permet de vérifier si l'élément est vide """
        return self.getAttributs() == {}

    def setAttribut(self, name, value):
        """
        Permet de définir un attribut du RTSS.

        Args:
            - name (str): Le nom de l'attribut à définir
            - value (any): La valeur de l'attribut
        """
        if not value: value = None
        self.attributs[name] = value

    def setAttributs(self, dict_atts:dict):
        """
        Permet de définir les attributs du RTSS.

        Args:
            dict_atts (dict): dictionnaire des attributs
        """
        for i, j in dict_atts.items(): self.setAttribut(i, j)