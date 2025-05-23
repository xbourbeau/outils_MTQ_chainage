# -*- coding: utf-8 -*-
import webbrowser
from qgis.core import QgsApplication
from qgis.gui import QgsMapTool, QgsMapCanvas

from ..mtq.core import  Geocodage
from ..mtq.fnt import reprojectGeometry

class MtqMapToolOpenSVN(QgsMapTool):  
    def __init__(self, canvas:QgsMapCanvas, geocode:Geocodage):
        # Class de géocodage
        self.geocode = geocode
        self.layer_rtss = None
        QgsMapTool.__init__(self, canvas)
        self.mCursor = QgsApplication.getThemeCursor(3)

    def activate(self):
        """ Méthode appelée quand l'outil est activé """
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
    
    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)

    def canvasPressEvent(self, e):
        default_link = """http://ws.sigvideo.mtq.min.intra/Interface/VisionneuseVideo.aspx?"""
        # Geometrie du point dans la projection de la couche des RTSS
        point_on_rtss = self.geocode.geocoderPointOnRTSS(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        center_point = reprojectGeometry(point_on_rtss.getGeometry(), self.layer_rtss.crs(), 4269).asPoint()
        if center_point.x() != 0.0 or center_point.y() != 0.0:
            default_link = f'''{default_link}x={center_point.x()}&y={center_point.y()}&projection=EPSG_4269_DEC&zoneTampon=5'''
        webbrowser.open_new(default_link)
    
    def deactivate(self):
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            self.canvas().unsetMapTool(self)
            # Désactiver l'outil
            QgsMapTool.deactivate(self)
        
        
        