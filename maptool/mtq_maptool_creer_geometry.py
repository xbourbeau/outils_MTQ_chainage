# -*- coding: utf-8 -*-
from qgis.core import QgsGeometry, QgsApplication, QgsProject, QgsFeature, QgsWkbTypes, Qgis
from qgis.gui import QgsMapTool, QgsMapToolEdit, QgisInterface, QgsMapCanvas, QgsAttributeEditorContext
from PyQt5.QtCore import Qt
from qgis.PyQt.QtWidgets import QMenu
from qgis.PyQt.QtGui import QKeySequence

from ..modules.PluginParametres import PluginParametres
from ..modules.TemporaryGeometry import TemporaryGeometry
from ..mtq.core import Geocodage, PointRTSS, LineRTSS, PolygonRTSS
from ..mtq.functions import reprojectGeometry

class MtqMapToolCreerGeometry(QgsMapToolEdit):
    
    def __init__(self, iface:QgisInterface, geocode:Geocodage):
        # Objet de géocodage
        self.geocode = geocode
        self.iface = iface
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapToolEdit.__init__(self, iface.mapCanvas())
        # Référence aux paramètres
        self.params = PluginParametres()
        # Définition du curseur
        self.mCursor = QgsApplication.getThemeCursor(4)
        self.layer_rtss = None
    
    def activate(self):
        # Définir les variables utilisé pour le snap parralèl
        self.show_parralel_snap, self.snap_offset = False, 0
        # Définir les variables utilisé pour le snap perpendiculaire
        self.show_perpendicular_snap, self.snap_chainage = False, 0
        # Activer le curseur
        self.canvas().setCursor(self.mCursor)
        # Cérer les géometries temporaires du maptool
        self.new_point_marker = TemporaryGeometry.createMarkerNewPoint(self.canvas())
        
        self.new_geom = TemporaryGeometry.createNewGeom(self.canvas())
        self.new_geom_prolg = TemporaryGeometry.createNewGeomProlongation(self.canvas())

        self.snap_line_parralel = TemporaryGeometry.createSnappingLine(self.canvas())
        self.snap_line_perpendiculair = TemporaryGeometry.createSnappingLine(self.canvas())

        self.iface.currentLayerChanged.connect(self.setActiveLayer)
        self.setActiveLayer()

        self.reset()
    
    def reset(self):
        """ Réinitialiser l'outil """
        # Cacher les géometries temporaire
        self.new_geom.hide()
        self.new_geom_prolg.hide()
        self.new_point_marker.hide()
        # Redéfinir les Géometries RTSS des nouvelles entitées
        self.feat_rtss = None
        self.current_pt_rtss = None
        self.previous_pt_rtss = None
        self.list_points = []
        self.line_rtss = LineRTSS([])
        self.polygon_rtss = PolygonRTSS([])

    def setActiveLayer(self):
        self.active_layer = self.currentVectorLayer()
        # TODO: Test for QGIS v. avant 3.30
        try: self.geom_type = self.active_layer.geometryType()
        except: self.geom_type = -1
        self.reset()

    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)

    def canvasPressEvent(self, e):
        """
        Méthode activé quand la carte est cliquée

        Args:
            - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
        """
        if self.active_layer == 0: return None
        if not self.active_layer.isEditable(): return None

        # Click Gauche    
        if e.button() == 1:
            self.previous_pt_rtss = self.current_pt_rtss
            if not self.feat_rtss: self.feat_rtss = self.geocode.get(self.previous_pt_rtss.getRTSS())
            
            # Point
            if self.geom_type == 0:
                point_geom = self.feat_rtss.geocoderPoint(self.previous_pt_rtss)
                # Projeter le point sur le RTSS dans la projection de la carte
                point_geom = self.toMapCoordinates(self.layer_rtss, point_geom.asPoint())
                point_geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.active_layer, point_geom))
                self.createNewFeature(point_geom)
            
            else: 
                self.list_points.append(self.previous_pt_rtss)
                
                # Line
                if self.geom_type == 1: object_rtss = self.createLine(self.list_points)
                # Polygon
                elif self.geom_type == 2: object_rtss = self.createPolygon(self.list_points)
                else: object_rtss=LineRTSS([])

                if object_rtss.hasOneRTSS() and object_rtss.isValide():
                    self.new_geom.setToGeometry(self.feat_rtss.geocoder(object_rtss))
                    self.new_geom.show()
                else: self.new_geom.hide()
                self.new_geom_prolg.hide()

        # Click Droit
        else: 
            if self.geom_type == 1 or self.geom_type == 2:
                geom = reprojectGeometry(self.new_geom.asGeometry(), QgsProject.instance().crs(), self.active_layer.crs())
                if geom.isGeosValid(): return self.createNewFeature(geom)
            self.reset()
    
    def canvasMoveEvent(self, e):
        """
        Méthode activé quand le curseur se déplace dans la carte

        Args:
            - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur dans la carte
        """
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        # Get infos du RTSS le plus proche du cursor
        if self.feat_rtss: self.current_pt_rtss = self.feat_rtss.geocoderInversePoint(geom)
        else: self.current_pt_rtss = self.geocode.geocoderInversePoint(geom)
        # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
        if self.current_pt_rtss is None : return self.new_point_marker.hide()

        self.setSnapParralelLine()
        self.setSnapPerpendicularlLine()
        
        if self.geom_type == 0:
            point_geom = self.geocode.geocoderPoint(self.current_pt_rtss)
            # Projeter le point sur le RTSS dans la projection de la carte
            point_geom = self.toMapCoordinates(self.layer_rtss, point_geom.asPoint())
            self.new_point_marker.setCenter(point_geom)
            # Afficher le le marker de RTSS dans la carte
            self.new_point_marker.show()

        elif self.list_points:
            list_point_temp = [self.list_points[-1], self.current_pt_rtss]
            
            # Line
            if self.geom_type == 1 or len(self.list_points) == 1: object_rtss = self.createLine(list_point_temp)
            # Polygon
            elif self.geom_type == 2: object_rtss = self.createPolygon([self.list_points[0]] + list_point_temp)
            else: object_rtss=LineRTSS([])

            if object_rtss.hasOneRTSS() and object_rtss.isValide():
                self.new_geom_prolg.setToGeometry(self.feat_rtss.geocoder(object_rtss))
                self.new_geom_prolg.show()
            else: self.new_geom_prolg.hide()

    def createPolygon(self, points=list[PointRTSS]):
        return PolygonRTSS(points + [points[0]])

    def createLine(self, points=list[PointRTSS]):
        return LineRTSS(points)

    def createNewFeature(self, geom:QgsGeometry):
        """
        Permet de créer l'entité selon la couche active à partir de la géometrie tracé.

        Args:
            - geom (QgsGeometry) = La géometrie tracer pour la nouvelle entitée
        """
        # Créer une entitée
        new_feat = QgsFeature(self.active_layer.fields())
        new_feat.setGeometry(geom)

        # Vérifier si la couche à des champs à remplir
        if self.active_layer.fields().count():
            # Cacher la géometrie du prolongement
            self.new_geom_prolg.hide()
            # Créer le formulaire pour les attibuts
            attribute_form = self.iface.getFeatureForm(self.active_layer, new_feat)
            attribute_form.setMode(QgsAttributeEditorContext.AddFeatureMode)
            attribute_form.accepted.connect(self.reset)
            attribute_form.rejected.connect(self.reset)
            attribute_form.show()
        # Sinon ajouter l'entité à la couche
        else:
            self.active_layer.addFeature(new_feat)
            self.reset()

    def setSnapParralelLine(self):
        if self.show_parralel_snap:
            feat_rtss = self.geocode.get(self.current_pt_rtss.getRTSS())
            self.current_pt_rtss.setOffset(self.snap_offset)
            line_geom = feat_rtss.asLineRTSS(offset=self.snap_offset)
            self.snap_line_parralel.setToGeometry(feat_rtss.geocoderLine(line_geom))
            self.snap_line_parralel.show()
        else: self.snap_line_parralel.hide()

    def setSnapPerpendicularlLine(self):
        if self.show_perpendicular_snap:
            length = self.canvas().extent().perimeter()/4
            feat_rtss = self.geocode.get(self.current_pt_rtss.getRTSS())
            self.current_pt_rtss.setChainage(self.snap_chainage)
            line_geom = feat_rtss.getTransect(chainage=self.snap_chainage, dist_d=length, dist_g=length)
            self.snap_line_perpendiculair.setToGeometry(line_geom)
            self.snap_line_perpendiculair.show()
        else: self.snap_line_perpendiculair.hide()

    def keyPressEvent(self, e):
        # Vérifier le raccourci clavier pour le snap parralele 
        if QKeySequence(self.params.getValue("raccourcis_clavier_parralele")).matches(QKeySequence(e.key())) == 2:
            self.show_parralel_snap = not self.show_parralel_snap
            if self.previous_pt_rtss: self.snap_offset = self.previous_pt_rtss.getOffset()
            else: self.snap_offset = self.current_pt_rtss.getOffset()
            self.setSnapParralelLine()
        # Vérifier le raccourci clavier pour le snap perpendiculaire
        if QKeySequence(self.params.getValue("raccourcis_clavier_perpendiculaire")).matches(QKeySequence(e.key())) == 2:
            self.show_perpendicular_snap = not self.show_perpendicular_snap
            if self.previous_pt_rtss: self.snap_chainage = self.previous_pt_rtss.getChainage()
            else: self.snap_chainage = self.current_pt_rtss.getChainage()
            self.setSnapPerpendicularlLine()
    
    def deactivate(self):
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            # Retirer de la carte les géometries créées
            self.canvas().scene().removeItem(self.snap_line_perpendiculair)
            self.canvas().scene().removeItem(self.snap_line_parralel)
            self.canvas().scene().removeItem(self.new_point_marker)
            self.canvas().scene().removeItem(self.new_geom_prolg)
            self.canvas().scene().removeItem(self.new_geom)

            self.iface.currentLayerChanged.disconnect(self.setActiveLayer)

            self.canvas().unsetMapTool(self)
            # Désactiver l'outil
            QgsMapTool.deactivate(self)    

