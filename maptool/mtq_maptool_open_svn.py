# -*- coding: utf-8 -*-
import os
import webbrowser

from qgis.core import QgsGeometry
from qgis.gui import QgsMapTool

from ..mtq.fnt import reprojectGeometry

class MtqMapToolOpenSVN(QgsMapTool):  
    def __init__(self, canvas, geocode, layer_rtss):
        QgsMapTool.__init__(self, canvas)
        # Reference de la carte
        self.canvas = canvas
        # Class de géocodage
        self.geocode = geocode
        self.layer_rtss = layer_rtss
        
        # Le QgsMapTool actif dans la carte avant cette outils
        self.last_maptool = None

    ''' Function pour definir un QgsMapTool à rendre actif lorsque celui-ci est désactivé. '''
    def lastMapTool(self, maptool):
        # Garder en mémoire le QgsMapTool à rendre actif lors de la désactivation
        self.last_maptool = maptool

    def canvasPressEvent(self, e):
        default_link = """http://ws.sigvideo.mtq.min.intra/Interface/VisionneuseVideo.aspx?"""
        #try: 
        # Geometrie du point dans la projection de la couche des RTSS
        point_on_rtss, num_rtss, chainage, dist = self.geocode.getPointOnRTSS(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        center_point = reprojectGeometry(point_on_rtss, self.canvas.mapSettings().destinationCrs(), 4326).asPoint()
        if center_point.x() != 0.0 or center_point.y() != 0.0:
            default_link = f"""http://ws.sigvideo.mtq.min.intra/Interface/VisionneuseVideo.aspx?x={center_point.x()}&y={center_point.y()}&projection=EPSG_4269_DEC&zoneTampon=5"""
        #except: pass
        webbrowser.open_new(default_link)
    
    def canvasReleaseEvent(self, e):
        self.deactivate()
    
    def deactivate(self):
        # Émettre le signal de desactivation de l'outil
        self.deactivated.emit()
        self.canvas.unsetMapTool(self)
        
        # Désactiver l'outil
        QgsMapTool.deactivate(self)
        # Essayer de remettre le dernier QgsMapTool actif
        if self.last_maptool:
            if self.last_maptool.action(): self.last_maptool.action().trigger()
            else: self.canvas.setMapTool(self.last_maptool)
        self.last_maptool = None
        
pass
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        