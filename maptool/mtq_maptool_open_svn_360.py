# -*- coding: utf-8 -*-
import webbrowser
from qgis.core import QgsApplication
from qgis.gui import QgsMapTool, QgsMapCanvas

from ..mtq.core import  Geocodage
from ..mtq.functions import reprojectGeometry

class MtqMapToolOpenSVN360(QgsMapTool):  
    def __init__(self, canvas:QgsMapCanvas, geocode:Geocodage):
        # Class de géocodage
        self.geocode = geocode
        self.layer_rtss = None
        # Définir la liste des epsg géréer par SVN360
        self.list_epsg = ["4326", "3799", "4617"]
        QgsMapTool.__init__(self, canvas)
        self.mCursor = QgsApplication.getThemeCursor(3)

    def activate(self):
        """ Méthode appelée quand l'outil est activé """
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
    
    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)

    def canvasPressEvent(self, e):
        # Lien SVN 360 par défault
        default_link = "https://svn360.mtq.min.intra"
        try:
            # Geometrie du point dans la projection de la couche des RTSS
            point_on_rtss = self.geocode.geocoderPointOnRTSS(self.toLayerCoordinates(self.layer_rtss, e.pos()))
            # Définir l'epsg de la couche des RTSS
            layer_epsg = self.layer_rtss.crs().authid().split(":")[-1]
            # Définir l'epsg à utiliser selon la couche et les epsg disponible
            if not layer_epsg in self.list_epsg: layer_epsg = 4326
            # Définir le point cliqué sur la route dans la bonne projection
            center_point = reprojectGeometry(point_on_rtss.getGeometry(), self.layer_rtss.crs(), layer_epsg).asPoint()
            # Ajpouter la postion au lient SVN 360
            default_link += f"?x={center_point.x()}&y={center_point.y()}&Epsg={layer_epsg}&rayon=50"
        except: pass
        # Ouvrir le lien web
        webbrowser.open_new(default_link)
    
    def deactivate(self):
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            self.canvas().unsetMapTool(self)
            # Désactiver l'outil
            QgsMapTool.deactivate(self)
        
        
        