# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSettings

class Parametre:
    """
    Un objet pour enregistrer et récupérer des paramètres personnalisée dans QGIS.

    Les paramètres sont enregistrer dans les paramètres avancées sous l'arboressance:
        - plugin_name/categorie/setting_name
    """
    
    __slots__ = ("setting", "default_value")
    
    def __init__(self, plugin_name:str, categorie:str, setting_name:str, default_value:any):
        """
        Permet d'instancier un objet Parametre.

        L'arboressance dans les paramètres avancée: plugin_name/categorie/setting_name

        Args:
            - plugin_name (str): Le nom du plugin dans l'arboressance
            - categorie (str): Le nom de la catégorie dans l'arboressance
            - setting_name (str): Le nom du paramètre
            - default_value (any): La valeur par défautl du paramètre
        """
        # Nom de la catégorie du plugin dans les settings de QGIS 
        self.default_value = default_value
        # Path to QGIS Setting
        self.setting = f"{plugin_name}/{categorie}/{setting_name}"
    
    def set(self, val):
        """ Permet de modifier la valeur du paramètre dans les settings de QGIS """
        QSettings().setValue(self.setting, val)
    
    def get(self)->str:
        """ Permet de retourner la valeur du parmamètre """
        return QSettings().value(self.setting, self.default_value)
    
    def getDefaultValue(self): return self.default_value