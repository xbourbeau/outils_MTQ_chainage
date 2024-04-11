# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsApplication
from qgis.gui import QgsMapToolIdentify, QgsMapTool
from PyQt5.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QMenu

class MtqMapToolSelectLayerValue(QgsMapToolIdentify):
    
    selectedValue = pyqtSignal(str)
    
    def __init__(self, canvas, layer, field_name):
        super(MtqMapToolSelectLayerValue, self).__init__(canvas)
        
        self.layer = layer
        self.field_name = field_name
        self.dict_rtss_geom = {}
        self.mCursor = QgsApplication.getThemeCursor(2)
    
    """ Méthode appelée quand l'outil est activé """
    def activate(self):
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
        self.last_flash = None
    
    def flashMenuItem(self, action):
        if self.last_flash != action.text():
            self.last_flash = action.text()
            self.canvas().flashGeometries([self.dict_rtss_geom[self.last_flash]], self.layer.crs(), flashes=2, duration=300)
    
    def canvasReleaseEvent(self, e):
        results = self.identify(e.pos().x(), e.pos().y(), [self.layer])
        if results:
            # If there's only one identified feature, return its field value directly
            if len(results) == 1:
                self.canvas().flashGeometries([results[0].mFeature.geometry()], self.layer.crs(), flashes=2, duration=300)
                self.selectedValue.emit(str(results[0].mFeature[self.field_name]))
            else:
                # If there are multiple identified features, show a menu to choose from
                menu = QMenu()
                # Faire clignoter la géometrie du RTSS dont la souris est par dessus dans le menu
                menu.hovered.connect(self.flashMenuItem)
                for result in results:
                    feature = result.mFeature
                    field_value = feature[self.field_name]
                    self.dict_rtss_geom[field_value] = feature.geometry()
                    action = menu.addAction(str(field_value))
                    action.triggered.connect(lambda _, value=str(field_value): self.selectedValue.emit(value))
                menu.exec_(e.globalPos())
                # Lorsque le choix est fait, déconnecter la méthode du menu
                menu.hovered.disconnect(self.flashMenuItem)
                self.dict_rtss_geom.clear()

pass