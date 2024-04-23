# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSettings
from .Parametre import Parametre

class ParametreFloat(Parametre):
    """
    Un objet pour enregistrer et récupérer un paramètre personnalisée dans QGIS.
    Le paramètre sera retourner sous forme de float

    Les paramètres sont enregistrer dans les paramètres avancées sous l'arboressance:
        - plugin_name/categorie/setting_name
    """
    
    __slots__ = ("setting", "default_value")

    def __init__(self, plugin_name:str, categorie:str, setting_name:str, default_value:float):
        """
        Permet d'instancier un objet ParametreFloat.

        L'arboressance dans les paramètres avancée: plugin_name/categorie/setting_name

        Args:
            - plugin_name (str): Le nom du plugin dans l'arboressance
            - categorie (str): Le nom de la catégorie dans l'arboressance
            - setting_name (str): Le nom du paramètre
            - default_value (float): La valeur par défautl du paramètre
        """
        Parametre.__init__(self, plugin_name, categorie, setting_name, default_value)
    
    def get(self):
        """ Permet de retourner la valeur du parmamètre en float"""
        return QSettings().value(self.setting, self.default_value, type=float)