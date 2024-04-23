# -*- coding: utf-8 -*-
from typing import Union
import uuid

# Librairie MTQ
from .RTSS import RTSS
from .LineSegmentationElement import LineSegmentationElement
from .PointRTSS import PointRTSS

class SegmentationPoint(PointRTSS):
    """
    Objet représentant une segmentation des éléments réseau sur un RTSS.
    Une segmentation possède un chainage unique sur le RTSS et contient une liste des éléments
    contenue au chainage. 
    Une segmentation peut également contenir des attributs.
    """
    __slots__ = ("rtss", "chainage", "offset", "geom", "dict_elements", "dict_attributs")
    
    def __init__(self,
                 rtss:Union[str, RTSS],
                 chainage:Union[str, RTSS, float, int],
                 elements:list[LineSegmentationElement]=[],
                 attributs={}):
        """
        Initialisation d'un objet SegmentationPoint

        Args:
            - rtss (RTSS): Le RTSS du point de segmentation
            - chainage (Chainage): Le chainage du point de segmentation
            - elements (dict): Liste des éléments contenu dans le point
            - attributs (dict): Attributs pouvant caractériser le point de segmentation
        """
        self.setElements(elements)
        self.dict_attributs = {}
        self.dict_attributs.update(attributs)
        PointRTSS.__init__(self, rtss, chainage)
    
    def __str__(self):  return f"{self.getRTSS()}, {self.getChainage()}: {self.dict_elements}"
        
    def __repr__(self): return f"SegmentationPoint {self.getRTSS()} ({self.getChainage()}): {self.dict_elements}"
    
    def copy(self): 
        return SegmentationPoint(
                rtss=self.getRTSS(),
                chainage=self.getChainage(),
                elements=self.getElements(),
                attributs=self.dict_attributs)
    
    def addElement(self, new_element:LineSegmentationElement): 
        """ Méthode qui permet d'ajouter un élément a la segmentation """
        if self.hasElement(new_element): 
            raise KeyError(f"L'indentifant {new_element.id()} de l'element existe deja "
                           f"dans le point de segmentation ({self.getChainage()})")
        self.dict_elements[new_element.id()] = new_element 
    
    def addElements(self, new_elements:list[LineSegmentationElement]):
        """ Méthode qui permet d'ajouter plusieurs éléments a la segmentation """
        for elem in new_elements: self.addElement(elem)
    
    def createElement(self, id=None, offset_d=0, offset_f=None, attributs={}, intepolate_on_rtss=True):
        if id is None: id = str(uuid.uuid4())
        return LineSegmentationElement(id=id,
                                       offset_d=offset_d,
                                       offset_f=offset_f,
                                       attributs=attributs,
                                       intepolate_on_rtss=intepolate_on_rtss)

    def createAndAddElement(self, id=None, offset_d=0, offset_f=None, attributs={}, intepolate_on_rtss=True):
        elem = self.createElement(id=id,
                                  offset_d=offset_d,
                                  offset_f=offset_f,
                                  attributs=attributs,
                                  intepolate_on_rtss=intepolate_on_rtss)
        #self.

    def getAttribut(self, attribut_name):
        """ Méthode qui permet de retourner une des valeurs d'attribut """
        return self.dict_attributs.get(attribut_name, None)
    
    def getElement(self, id): 
        """ Méthode qui permet de retourner les éléments associé au point de segmentation """
        return self.dict_elements.get(id, None)

    def getElements(self): 
        """ Méthode qui permet de retourner les éléments associé au point de segmentation """
        return list(self.dict_elements.values())
        
    def hasElement(self, element:LineSegmentationElement):
        return element.id() in self.dict_elements

    def isEmpty(self):
        """ Méthode qui permet de savoir si le point à des éléments associé """
        return self.getElements() == []
    
    def removeElement(self, element:LineSegmentationElement):
        """ Méthode qui permet de retirer un élément du dictionnaire """
        self.removeElementById(element.id())
    
    def removeElementById(self, element_id):
        """ Méthode qui permet de retirer un élément du dictionnaire """
        if element_id in self.dict_elements: self.dict_elements.pop(element_id)

    def setElements(self, elements:list[LineSegmentationElement]):
        """ Méthode pour initialiser les éléments asocier au point """
        self.dict_elements = {}
        self.addElements(elements)
    
    def updateAttribut(self, name, new_val):
        """ Méthode qui permet de modifier un attributs du point de segmentation """
        if name in self.dict_attributs: self.dict_attributs[name] = new_val