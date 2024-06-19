# -*- coding: utf-8 -*-
from qgis.core import QgsApplication, QgsMapLayer
from qgis.gui import QgsMapToolIdentifyFeature, QgsMapCanvas, QgsMapTool
from PyQt5.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QMenu

class MtqMapToolSelectLayerValue(QgsMapToolIdentifyFeature):
    
    selectedValue = pyqtSignal(str)
    
    def __init__(self, canvas:QgsMapCanvas, layer:QgsMapLayer, field_name:str, deactivate_on_identify=False):
        #super(MtqMapToolSelectLayerValue, self).__init__(canvas)
        QgsMapToolIdentifyFeature.__init__(self, canvas)
        self.field_name = field_name
        self.deactivate_on_identify = deactivate_on_identify
        self.setLayer(layer)
        self.mCursor = QgsApplication.getThemeCursor(4)
    
    def activate(self):
        """ Méthode appelée quand l'outil est activé """
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
        self.reset()

    def setLayer(self, layer:QgsMapLayer):
        if isinstance(layer, QgsMapLayer): self.layer_id = layer.id()
        else: self.layer_id = ""
    
    def reset(self):
        self.dict_geom = {}

    def canvasReleaseEvent(self, e):
        # Identifier le feature selon le clique
        results = self.identify(e.pos().x(), e.pos().y(), [self.layer(self.layer_id)])
        # Créer un dictionnaire avec le résultat 
        self.dict_geom = {str(result.mFeature[self.field_name]): result.mFeature.geometry() for result in results}
        if self.dict_geom == {}: return None
        # If there's only one identified feature, return its field value directly
        if len(self.dict_geom) == 1: result = str(results[0].mFeature[self.field_name])
        # If there are multiple identified features, show a menu to choose from
        else: result = self.showMenuChoix(e.globalPos())
            
        # Flash selected value
        self.canvas().flashGeometries([self.dict_geom[result]], self.layer(self.layer_id).crs(), flashes=2, duration=300)
        # Emit selected value
        self.selectedValue.emit(str(result))
        # Deactivate if specified
        if self.deactivate_on_identify: self.deactivate()
        else: self.reset()

    def showMenuChoix(self, pos):
        """ 
        Méthode qui permet de montrer le menu contenant
        les choixs de RTSS et de retourner le RTSS selectionné.
        """
        menu = QMenu()
        # Faire clignoter la géometrie du RTSS 
        # dont la souris est par dessus dans le menu
        menu.hovered.connect(self.flashMenuItem)
        self.last_flash = None
        # Ajouter les options au menu
        for val in self.dict_geom: menu.addAction(val)
        # Montrer le menu 
        choix = menu.exec_(pos)
        # Lorsque le choix est fait, déconnecter la méthode du menu
        menu.hovered.disconnect(self.flashMenuItem)
        
        if choix is None: return "" 
        else: return choix.text()

    def flashMenuItem(self, action):
        # Vérifier si l'entité ne vient pas d'être flashé 
        if action.text() != self.last_flash:
            # Garder en mémoire l'entité qui vient d'être flashé 
            self.last_flash = action.text()
            self.canvas().flashGeometries([self.dict_geom[action.text()]], self.layer(self.layer_id).crs(), flashes=2, duration=300)
        

    def deactivate(self):
        """ Méthode appelée quand l'outil est désactivé. """
        self.canvas().unsetMapTool(self)
        # Émettre le signal de desactivation de l'outil
        self.deactivated.emit()
        # Désactiver l'outil
        QgsMapTool.deactivate(self)