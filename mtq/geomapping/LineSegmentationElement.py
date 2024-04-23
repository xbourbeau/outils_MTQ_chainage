# -*- coding: utf-8 -*-
from typing import Dict

class LineSegmentationElement:
    """ Représente un Élément linéaire d'une segmentation """

    def __init__(self, id, offset_d, offset_f=None, attributs={}, intepolate_on_rtss=True):
        self.identifiant = id
        self.setOffsetDebut(offset_d)
        if offset_f is None: offset_f = offset_d
        self.setOffsetDebut(offset_f)
        self.attributs = attributs
        self.intepolate_on_rtss = intepolate_on_rtss
    
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

    def id(self):
        return self.identifiant

    def setAttribut(self, name, value):
        """
        Permet de définir un attribut du RTSS.

        Args:
            - name (str): Le nom de l'attribut à définir
            - value (any): La valeur de l'attribut
        """
        self.attributs[name] = value

    def setInterpolation(self, intepolate:bool):
        """ Permet de définir la valeur d'interpolation """
        self.intepolate_on_rtss = intepolate

    def setOffsetDebut(self, offset):
        """ Permet de définir la valeur de offset de début """
        self.offset_d = offset

    def setOffsetFin(self, offset):
        """ Permet de définir la valeur de offset de fin """
        self.offset_f = offset