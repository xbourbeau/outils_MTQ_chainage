# -*- coding: utf-8 -*-
from typing import Union
import copy
from qgis.core import QgsGeometry

# Librairie MTQ
from ..geomapping.RTSS import RTSS
from ..geomapping.Chainage import Chainage
from .LineSegmentationElement import LineSegmentationElement
from ..geomapping.PointRTSS import PointRTSS

class SegmentationPoint(PointRTSS):
    """
    Objet représentant une segmentation des éléments réseau sur un RTSS.
    Une segmentation possède un chainage unique sur le RTSS et contient une liste des éléments
    contenue au chainage. 
    Une segmentation peut également contenir des attributs.
    """
    __slots__ = ("rtss", "chainage", "offset", "geom", "elements", "attributs")
    
    def __init__(self,
                 rtss:Union[str, RTSS],
                 chainage:Union[str, Chainage, float, int],
                 elements:list[LineSegmentationElement]=[],
                 **kwargs):
        """
        Initialisation d'un objet SegmentationPoint

        Args:
            - rtss (RTSS): Le RTSS du point de segmentation
            - chainage (Chainage): Le chainage du point de segmentation
            - elements (dict): Liste des éléments contenu dans le point
            - **kwargs: Attributs pouvant caractériser le point de segmentation
        """
        # Créer la sous-classe du PointRTSS
        PointRTSS.__init__(self, rtss, chainage)
        # Initialiser les éléments de la segmentation
        self.setElements(elements)
        # Ajouter les attributs du point de segmentation
        self.attributs = kwargs
    
    @classmethod
    def fromPointRTSS(cls, point_rtss:PointRTSS, elements:list[LineSegmentationElement]=[], **kwargs):
        """
        Initialisation d'un objet SegmentationPoint à partir d'un PointRTSS.

        Args:
            - point_rtss (PointRTSS): Le point de segmentation
            - elements (list): Liste des éléments contenu dans le point
            - kwargs: Attributs pouvant caractériser le point de segmentation
        """
        return cls(point_rtss.getRTSS(), point_rtss.getChainage(), elements, **kwargs)
    
    def __str__(self):  
        if self.isEnd(): elements = " End"
        else: elements = f" Elements: {[str(elem) for elem in self.elements]}"
        
        if self.attributs == {}: atts = ""
        else: atts = self.attributs

        return f"{self.getRTSS()}, {self.getChainage()} {atts}{elements}"
        
    def __repr__(self): return f"SegmentationPoint {str(self)}"
    
    def __contains__(self, key): return self.hasElement(key)

    def __iter__ (self): return self.elements.__iter__()

    def __deepcopy__(self, memo):
        new_obj = self.__class__.__new__(self.__class__)

        # Add the new object to the memo dictionary to avoid infinite recursion
        memo[id(self)] = new_obj

        # Deep copy all the attributes
        for slot in self.__slots__:
            v = getattr(self, slot)
            # Use the copy method for QgsGeometry objects
            if isinstance(v, QgsGeometry): setattr(new_obj, slot, QgsGeometry(v))
            else: setattr(new_obj, slot, copy.deepcopy(v, memo))

        return new_obj

    def copy(self): 
        return SegmentationPoint(
                rtss=self.getRTSS(),
                chainage=self.getChainage(),
                elements=self.getElements(),
                attributs=self.attributs)
    
    def addElement(self, new_element:LineSegmentationElement): 
        """ Méthode qui permet d'ajouter un élément a la segmentation """
        if self.hasElement(new_element): 
            raise KeyError(f"L'élément ({new_element}) existe deja "
                           f"dans le point de segmentation ({self.getChainage()})")
        self.elements.append(new_element)
    
    def addElements(self, new_elements:list[LineSegmentationElement]):
        """ Méthode qui permet d'ajouter plusieurs éléments a la segmentation """
        for elem in new_elements: self.addElement(elem)
    
    def createElement(self, offset_d=0, offset_f=None, intepolate_on_rtss=True, **kwargs):
        """ Méthode qui permet de créer un élément de segmentation """
        return LineSegmentationElement(
            offset_d=offset_d,
            offset_f=offset_f,
            intepolate_on_rtss=intepolate_on_rtss,
            **kwargs)

    def createAndAddElement(self, offset_d=0, offset_f=None, intepolate_on_rtss=True, **kwargs):
        """ Méthode qui permet de créer et ajouter un élément de segmentation """
        elem = self.createElement(
            offset_d=offset_d,
            offset_f=offset_f,
            intepolate_on_rtss=intepolate_on_rtss,
            **kwargs)
        self.addElement(elem)
        return elem

    def getAttribut(self, attribut_name):
        """ Méthode qui permet de retourner une des valeurs d'attribut """
        return self.attributs.get(attribut_name, None)

    def getElements(self): 
        """ Méthode qui permet de retourner les éléments associé au point de segmentation """
        return self.elements

    def getValues(self, elem_attribut_name):
        """ Permet de retourner les valeurs unique d'un attribut de tous les éléments """
        # Liste des valeurs 
        values = []
        # Parcourir les éléments du point de segmentation
        for elem in self.getElements():
            # Aller chercher la valeurs de l'attribut pour l'élément
            value = elem.getAttribut(elem_attribut_name)
            # Ajouter la valeurs d'attribut retourner si elle existe
            if value: values.append(value)
        # Retourner seulement les elements unique
        return list(set(values))
    
    def getUniqueValue(self, elem_attribut_name):
        values = self.getValues(elem_attribut_name)
        if values == []: return None
        else: return values[0]
        
    def hasElement(self, element:LineSegmentationElement):
        return element in self.elements

    def isEmpty(self):
        """ Méthode qui permet de savoir si le point à des éléments associé """
        return self.getElements() == []

    def isEnd(self):
        """
        Méthode qui permet de savoir si le point de segmentation est une fin.
        Donc que celui-ci n'a pas d'élément associé.
        """
        return self.isEmpty()
    
    def info(self):
        """ Méthode qui permet de print dans la console les infos du point """
        print(f"PointSegmentation ({self.getChainage()})")
        self.infoAttributs()
        self.infoElements()

    def infoAttributs(self):
        if self.attributs == {}: return None
        print("Attributs:")
        # Print les info des attributs
        for att, val in self.attributs.items():
            print(f"   - {att}: {val}")

    def infoElements(self):
        if self.isEnd(): print("End")
        else:
            print("Elements:")
            for elem in self.getElements():
                print(f"   - {str(elem)}")


    def removeElement(self, element:LineSegmentationElement):
        """ Méthode qui permet de retirer un élément de la liste """
        # Parcourir les éléments du point de segmentation
        for elem in self.getElements():
            # Retirer l'élément s'il est dans la liste
            if elem == element: return self.elements.remove(elem) is None
        return False

    def setElements(self, elements:list[LineSegmentationElement]):
        """ Méthode pour initialiser les éléments asocier au point """
        self.elements:list[LineSegmentationElement] = []
        self.addElements(elements)
    
    def updateAttribut(self, name, new_val):
        """ Méthode qui permet de modifier ou ajouter un attributs du point de segmentation """
        self.attributs[name] = new_val