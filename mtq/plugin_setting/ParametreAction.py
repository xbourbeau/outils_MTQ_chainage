# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSettings
from .Parametre import Parametre

class ParametreAction(Parametre):
    """
    Un objet pour enregistrer et récupérer une configuration d'Action personnalisée dans QGIS.

    Les paramètres sont enregistrer dans les paramètres avancées sous l'arboressance:
        - plugin_name/categorie/setting_name
    """
    
    __slots__ = ("setting", "default_value", "nom", "groupe", "icon")

    def __init__(self, plugin_name:str, nom:str, icon:str, setting_name:str, visible_by_default:bool=True, groupe:str=None):
        """
        Permet d'instancier un objet ParametreAction.

        L'arboressance dans les paramètres avancée: plugin_name/Action/setting_name

        Args:
            - plugin_name (str): Le nom du plugin dans l'arboressance
            - nom (str): Le nom de l'action
            - icon (str): Le chemin d'accèss vers l'icon
            - setting_name (str): Le nom du paramètre
            - visible_by_default (bool): Est-ce que l'action est visible
            - groupe ()
        """
        Parametre.__init__(self, plugin_name, "Action", setting_name, visible_by_default)
        self.nom = nom
        self.groupe = groupe
        self.icon = icon
    
    def get(self, defaut=False):
        """ Permet de retourner si l'action est visible """
        if defaut: return self.default_value
        else: return QSettings().value(self.setting, self.default_value, type=bool)
    
    def getIcon(self):
        """ Permet de retoruner l'icon associé à l'action """
        return self.icon
    
    def getGroupe(self):
        """ Permet de retourner le groupe de l'action """
        if not self.groupe: return ''
        else: return self.groupe