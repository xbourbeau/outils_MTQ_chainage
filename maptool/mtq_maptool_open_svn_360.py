# -*- coding: utf-8 -*-
import math
from qgis.core import QgsWkbTypes, QgsPointXY
from qgis.gui import QgsMapTool, QgsMapCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from ..mtq.core import  Geocodage, SVN360, LocalisationSVN
from ..mtq.fnt import reprojectGeometry
from ..modules.PluginParametres import PluginParametres
from ..modules.TemporaryGeometry import TemporaryGeometry

class MtqMapToolOpenSVN360(QgsMapTool):

    def __init__(self, canvas:QgsMapCanvas, geocode:Geocodage):
        # Class de géocodage
        self.geocode = geocode
        self.layer_rtss = None
        # Rayon par défaut à utiliser
        self.rayon = 10
        QgsMapTool.__init__(self, canvas)
        # Définir le module de paramètres
        self.params = PluginParametres()
        # Définir le module SVN360
        self.svn = SVN360()
        
        # Définir le cursor personnalisé
        cursor_pixmap = self.params.getPixmap("svn_cursor")
        cursor_pixmap = cursor_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.mCursor = QCursor(cursor_pixmap, cursor_pixmap.width()//2, cursor_pixmap.height()//2)

    def activate(self):
        """ Méthode appelée quand l'outil est activé """
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
        # Définir les 2 géométries temporaires pour faire la flèche
        self.arrow = TemporaryGeometry.createNewGeomArrow(self.canvas())
        self.line = TemporaryGeometry.createNewGeomArrow(self.canvas())
        # Démarrer la session SV360 avec les authentification de l'utilisateur courant
        self.svn.start_session()

        self.reset()

    def reset(self):
        # Lien SVN 360 par défault
        self.first_point_on_rtss = None
        # Chacher les géométries temporaires
        self.arrow.hide()
        self.line.hide()
        # Reset les points de la flèche temporaire dans la carte
        self.fleche_pt_1 = None
        self.fleche_pt_2 = None
        # Reset la localisation pour SVN
        self.loc:LocalisationSVN = None
    
    def setLayer(self, layer_id):
        self.layer_rtss = self.layer(layer_id)
        # Définir l'epsg de la couche des RTSS
        self.layer_epsg = self.layer_rtss.crs().authid().split(":")[-1]
        # Définir l'epsg à utiliser selon la couche et les epsg disponible
        if not self.layer_epsg in self.svn.list_epsg_possible: self.layer_epsg = 4326

    def canvasPressEvent(self, e):
        self.reset()
        try:
            # Click Gauche    
            if e.button() == 1:
                self.first_point_on_rtss = self.toLayerCoordinates(self.layer_rtss, e.pos())
                self.fleche_pt_1 = self.toMapCoordinates(self.layer_rtss, self.first_point_on_rtss)
                # Geometrie du point dans la projection de la couche des RTSS
                point_on_rtss = self.geocode.geocoderPointOnRTSS(self.first_point_on_rtss)
                # Définir le point cliqué sur la route dans la bonne projection
                center_point = reprojectGeometry(point_on_rtss.getGeometry(), self.layer_rtss.crs(), self.layer_epsg).asPoint()
                # Définir le point de localisation pour l'ouverture de SVN360
                self.loc = self.svn.create_loc_from_point(center_point, self.layer_epsg)
        except: self.reset()
    
    def canvasMoveEvent(self, e):
        """
        Méthode activé quand le curseur se déplace dans la carte
        Entrée:
            - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur
                                    dans la carte
        """
        # Skip si le premier point n'est pas encore défini 
        if self.fleche_pt_1 is None: return
        # Définir le deuxième point de la flèche
        self.fleche_pt_2 = self.toMapCoordinates(self.layer_rtss, self.toLayerCoordinates(self.layer_rtss, e.pos()))
        # Dessiner la flèche
        self.draw_arrow()

    def canvasReleaseEvent(self, e):
        """ Méthode appelée quand le bouton de la souris est relaché """
        # Skip si le premier point n'est pas encore défini
        if self.first_point_on_rtss is None: return
        self.arrow.hide()
        self.line.hide()
        # Geometrie du point dans la projection de la couche des RTSS
        last_point_on_rtss = self.toLayerCoordinates(self.layer_rtss, e.pos())
        # Définir l'azimut horizontal
        if self.first_point_on_rtss.distance(last_point_on_rtss) <= 1: h_az = None
        else: 
            # Calculer l'azimut en degres pour une localisation donnée.
            az_svn = self.svn.get_azimuth(self.loc, rayon=self.rayon)
            # Si l'azimut est null, alors on considère que l'angle horizontal n'est pas défini
            # (probablement parce que la localisation n'a pas d'images dans SVN360)
            if az_svn is None: h_az = None
            else: h_az = 360 - (az_svn - self.first_point_on_rtss.azimuth(last_point_on_rtss))
        # Ouvrir SVN360 avec les paramètres définies
        self.svn.open(self.loc, rayon=self.rayon, ahoriz=h_az)
        # Reset pour le prochain usage
        self.reset()

    def draw_arrow(self):
        """Draw an arrow head at the end of the line"""
        if self.fleche_pt_1 and self.fleche_pt_2:
            
            angle = math.atan2(self.fleche_pt_2.y() - self.fleche_pt_1.y(), self.fleche_pt_2.x() - self.fleche_pt_1.x())
            
            arrow_length = 20
            
            map_units_per_pixel = self.canvas().mapUnitsPerPixel()
            arrow_length_map = arrow_length * map_units_per_pixel
            
            left_angle = angle + math.radians(150)
            left_x = self.fleche_pt_2.x() + arrow_length_map * math.cos(left_angle)
            left_y = self.fleche_pt_2.y() + arrow_length_map * math.sin(left_angle)
            left_point = QgsPointXY(left_x, left_y)
            
            right_angle = angle - math.radians(150)
            right_x = self.fleche_pt_2.x() + arrow_length_map * math.cos(right_angle)
            right_y = self.fleche_pt_2.y() + arrow_length_map * math.sin(right_angle)
            right_point = QgsPointXY(right_x, right_y)
            
            self.arrow.reset(QgsWkbTypes.LineGeometry)
            self.arrow.addPoint(left_point)
            self.arrow.addPoint(self.fleche_pt_2)
            self.arrow.addPoint(right_point)

            self.line.reset(QgsWkbTypes.LineGeometry)
            self.line.addPoint(self.fleche_pt_1)
            self.line.addPoint(self.fleche_pt_2)
            
            self.line.show()
            self.arrow.show()

    def deactivate(self):
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            # Retirer les Géometrie temporaire
            self.canvas().scene().removeItem(self.arrow)
            self.canvas().scene().removeItem(self.line)

            self.canvas().unsetMapTool(self)
            # Désactiver l'outil
            QgsMapTool.deactivate(self)
        