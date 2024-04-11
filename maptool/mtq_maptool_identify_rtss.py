# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsGeometry
from qgis.gui import QgsMapTool
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMenu

from ..gestion_parametres import sourceParametre

class MtqMapToolIdentifyRTSS(QgsMapTool):
    
    identifyRTSS = pyqtSignal(str)
    
    def __init__(self, canvas, layer_rtss, geocode):
        # Reference de la carte
        self.canvas = canvas
        # Class de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = layer_rtss
        # Class de gestion des paramètres
        self.gestion_parametre = sourceParametre()
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapTool.__init__(self, self.canvas)
        # Garder en mémoire le QgsMapTool actif dans la carte
        self.last_maptool = self.canvas.mapTool()

    '''
    Méthode activé quand la carte est cliquée
    Paramètre entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
    '''
    def canvasReleaseEvent(self, e):
        # Click Gauche    
        if e.button() == 1:
            # Geometrie du point dans la projection de la couche des RTSS
            geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
            # RTSS le plus proche du click
            rtss_proche = self.geocode.nearestRTSS(geom, 1)
            # Distance de recherche(m) selon le paramètre de QGIS 
            search_dist = self.canvas.scale() * (self.searchRadiusMM()/1000)
            # Liste des RTSS à distance de recherche(m) du click
            rtss_proche = [val for val in rtss_proche if val['distance'] <= search_dist]
            # Si un RTSS est dans la tolérence
            if rtss_proche:
                feat_rtss = rtss_proche[0]['rtss']
                # Flasher la géometrie survolé
                self.canvas.flashGeometries([feat_rtss.getGeometry()], self.geocode.crs, flashes=2, duration=350)
                # Définir le numéro de RTSS (formater ou non selon le paramètre du plugin)
                rtss = feat_rtss.getRTSS(formater=self.gestion_parametre.getParam("formater_rtss").getValue())
                # Emmetre la géometrie
                self.identifyRTSS.emit(rtss)
        # Click Droit
        else: self.deactivate()
        
    '''
        Méthode appelée quand l'outil est désactivé
    '''
    def deactivate(self):
        
        # Émettre le signal de desactivation de l'outil
        self.deactivated.emit()
        
        # Sinon, retirer le QgsMapTool de selection d'un RTSS sur la carte
        if self.isActive(): self.canvas.unsetMapTool(self)
        
        # Désactiver l'outil
        QgsMapTool.deactivate(self)
        # Essayer de remettre le dernier QgsMapTool actif
        if self.last_maptool: self.canvas.setMapTool(self.last_maptool)
        #self.last_maptool = None
        self.clean()

pass
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        