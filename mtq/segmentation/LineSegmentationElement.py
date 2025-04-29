# -*- coding: utf-8 -*-
from typing import Dict

import copy

class LineSegmentationElement:
    """ Représente un Élément linéaire d'une segmentation """
    
    __slots__ = ("offset_d", "offset_f", "attributs", "intepolate_on_rtss")

    def __init__(self, offset_d=0, offset_f=None, intepolate_on_rtss=True, **kwargs):
        """
        Construcuteur par défault d'un objet LineSegmentationElement.

        Args:
            offset_d (float, optional): Le offset de début de l'élément. Defaults to 0.
            offset_f (float, optional): Le offset de fin de l'élément ou None représente une ligne parralèle. Defaults to None.
            intepolate_on_rtss (bool, optional): Indiquateur que le géocodage devrait se faire en suivant le RTSS. Defaults to True.
            **kwargs: Les attributs de l'élément
        """
        self.setOffsetDebut(offset_d)
        self.setOffsetFin(offset_f)
        self.setInterpolation(intepolate_on_rtss)
        self.attributs = {}
        # Set les attributs de l'élément 
        self.setAttributs(kwargs)
        #self.attributs = kwargs
    
    def __str__(self):
        # Définir la représentation des attributs
        attributs = f"Values: {self.getAttributs()}"
        # Retrourne les attributs seulement si les offset sont 0
        if self.isOnRTSS(): return attributs
        # Retourne un offset et les attributs si la ligne est parralèle
        elif self.isParallel(): return f"Offset: {self.getOffsetDebut()} {attributs}"
        # Sinon retourne les 2 offsets et les attributs
        else: return f"Offsets: ({self.getOffsetDebut()}, {self.getOffsetFin()}) {attributs}"
    
    def __repr__(self): return f"LineSegmentationElement {str(self)}"
    
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
        return self.offset_d
    
    def getOffsetFin(self):
        """ Permet de retourner le offset de fin """
        return self.offset_f

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

    def setInterpolation(self, intepolate:bool):
        """ Permet de définir la valeur d'interpolation """
        self.intepolate_on_rtss = intepolate

    def setOffsetDebut(self, offset):
        """ Permet de définir la valeur de offset de début """
        self.offset_d = offset

    def setOffsetFin(self, offset):
        """ Permet de définir la valeur de offset de fin """
        if offset is None: self.offset_f = self.offset_d
        else: self.offset_f = offset