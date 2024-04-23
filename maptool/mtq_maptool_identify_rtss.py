# -*- coding: utf-8 -*-

from qgis.core import QgsGeometry, QgsVectorLayer
from qgis.gui import QgsMapTool, QgsMapCanvas
from PyQt5.QtCore import pyqtSignal
from mtq.core import Geocodage

from ..modules.PluginParametres import PluginParametres

class MtqMapToolIdentifyRTSS(QgsMapTool):
    
    identifyRTSS = pyqtSignal(str)
    
    def __init__(self, canvas:QgsMapCanvas, layer_rtss:QgsVectorLayer, geocode:Geocodage):
        """ 
        Outil pour selectionner un RTSS dans la carte

        Args:
            canvas (QgsMapCanvas): Référence à la carte
            layer_rtss (QgsVectorLayer): La couche des RTSS
            geocode (Geocodage): Le module de géocodage
        """
        # Class de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = layer_rtss
        # Class de gestion des paramètres
        self.params = PluginParametres()
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapTool.__init__(self, canvas)
        # Garder en mémoire le QgsMapTool actif dans la carte
        self.last_maptool = self.canvas().mapTool()

    def canvasReleaseEvent(self, e):
        """
        Méthode activé quand la carte est cliquée
        Paramètre entrée:
            - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
        """
        # Click Gauche    
        if e.button() == 1:
            # Geometrie du point dans la projection de la couche des RTSS
            geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
            # Distance de recherche(m) selon le paramètre de QGIS 
            search_dist = self.canvas().scale() * (self.searchRadiusMM()/1000)
            # FeatRTSS le plus proche du click
            feat_rtss = self.geocode.nearestRTSS(geom, dist_max=search_dist)
            # Si un RTSS est dans la tolérence
            if feat_rtss:
                # Flasher la géometrie survolé
                self.canvas().flashGeometries([feat_rtss.geometry()], self.geocode.getCrs(), flashes=2, duration=350)
                # Définir le numéro de RTSS (formater ou non selon le paramètre du plugin)
                rtss = feat_rtss.value(formater=self.params.getValue("formater_rtss"))
                # Emmetre la géometrie
                self.identifyRTSS.emit(rtss)
        # Click Droit
        else: self.deactivate()

    def deactivate(self):
        """ Méthode appelée quand l'outil est désactivé """
        # Émettre le signal de desactivation de l'outil
        self.deactivated.emit()
        # Sinon, retirer le QgsMapTool de selection d'un RTSS sur la carte
        if self.isActive(): self.canvas().unsetMapTool(self)
        # Désactiver l'outil
        QgsMapTool.deactivate(self)
        # Essayer de remettre le dernier QgsMapTool actif
        if self.last_maptool: self.canvas().setMapTool(self.last_maptool)
        self.clean()

pass
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        