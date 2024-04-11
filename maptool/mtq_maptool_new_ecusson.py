# -*- coding: utf-8 -*-
import os

from qgis.core import (QgsProject, QgsGeometry, QgsVectorLayerUtils, QgsCoordinateTransform, 
    QgsField, QgsVectorLayer, QgsExpressionContextUtils, QgsApplication)
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapTool
from PyQt5.QtCore import Qt, QPoint
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMenu
from qgis.PyQt.QtCore import QVariant

from ..gestion_parametres import sourceParametre
from ..mtq.fnt import reprojectGeometry, validateLayer
from ..functions.addLayerToMap import addLayerToMap

""" ========================= Outil Tracer un segment parallel ======================================= """
class MtqMapToolNewEcusson(QgsMapTool):
    
    def __init__(self, canvas, geocode):
        # Reference de la carte
        self.canvas = canvas
        # Class de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = None
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapTool.__init__(self, self.canvas)
        self.mCursor = QgsApplication.getThemeCursor(3)
        # Class qui gère l'enregistrement des paramètres
        self.gestion_parametre = sourceParametre()
        
    """ Réinitialiser l'outil """
    def reset(self):
        # Cacher l'indicateur de RTSS
        self.rtss_marker.hide()
        # Arrêter le tracage de l'outils
        self.is_tracing = False
    
    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)
    
    """ Méthode appelée quand l'outil est activé """
    def activate(self):
        # Définir le cursor à utiliser
        self.canvas.setCursor(self.mCursor)
        # Geometry temporaire de la position sur le RTSS
        self.rtss_marker = QgsVertexMarker(self.canvas)
        self.rtss_marker.setColor(QColor("#178e0c"))
        self.rtss_marker.setIconSize(10)
        self.rtss_marker.setIconType(QgsVertexMarker.ICON_X)
        self.rtss_marker.setPenWidth(3)
        
        field_name = self.gestion_parametre.getParam("layer_ecusson_field_route").getValue()
        field_name_classe = self.gestion_parametre.getParam("layer_ecusson_field_classe").getValue()
        
        self.layer_ecusson = validateLayer(self.gestion_parametre.getParam("layer_ecusson_name").getValue(), fields_name=[field_name], geom_type=0)
        if not self.layer_ecusson:
            self.layer_ecusson = self.createNewLayer()
            path_to_ecusson = os.path.join(self.gestion_parametre.getParam("ecusson_path").getValue(), "styles")
            QgsExpressionContextUtils.setLayerVariable(self.layer_ecusson, 'path_to_ecusson', path_to_ecusson)
        
        self.field_index = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name]
        if self.field_index: self.field_index = self.field_index[0]
        else: self.field_index = 0
        
        self.field_index_classe = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name_classe]
        if self.field_index_classe: self.field_index_classe = self.field_index_classe[0]
        else: self.field_index_classe = None
        
        self.layer_ecusson.willBeDeleted.connect(self.deactivate)
        self.reset()
    
    def createNewLayer(self):
        # Create layer
        layer_ecusson = QgsVectorLayer(f"point?crs={self.layer_rtss.crs().authid()}", self.gestion_parametre.getParam("layer_ecusson_name").getValue(), "memory")
        # Add fields
        field_route = self.gestion_parametre.getParam("layer_ecusson_field_route").getValue()
        field_class = self.gestion_parametre.getParam("layer_ecusson_field_classe").getValue()
        if field_route == '': field_route = "num_route"
        if field_class == field_route: field_class = "Classification"
        if field_class == '': field_class = "Classification"
        layer_ecusson.dataProvider().addAttributes([QgsField(field_route, QVariant.String), QgsField(field_class, QVariant.String)])
        layer_ecusson.updateFields()
        return addLayerToMap(self.canvas, layer_ecusson, style=self.gestion_parametre.getParam("layer_ecusson_style").getValue())
        
    """
    Méthode activé quand la carte est cliquée
    Paramètre entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
    """
    def canvasPressEvent(self, e):
        # Click Gauche    
        if e.button() == 1:
            # Geometrie du point dans la projection de la couche des RTSS
            geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
            # Get infos du RTSS le plus proche du cursor
            geom_on_rtss, num_rtss, chainage, dist = self.geocode.getPointOnRTSS(geom)
            point_on_rtss = geom_on_rtss.asPoint()
            # Vérifier si le curseur est dans la distance de tolérance de QGIS avec le RTSS
            if dist <= self.canvas.scale() * (self.searchRadiusMM()/1000):
                # Placer le marker sur le point du RTSS 
                if self.layer_rtss.crs() != QgsProject.instance().crs(): point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss)
                self.rtss_marker.setCenter(point_on_rtss)
                att = {self.field_index: str(int(num_rtss[:5]))}
                # Ajouter la classification fonctionnelle si possible
                if self.field_index_classe:
                    feats = [feat for feat in self.layer_rtss.getFeatures(f"\"{self.gestion_parametre.getParam('field_num_rtss').getValue()}\" = '{num_rtss}'")]
                    if feats: att[self.field_index_classe] = feats[0][self.gestion_parametre.getParam('field_classification').getValue()]
                    else: att[self.field_index_classe] = '00'
                geom_on_rtss = reprojectGeometry(geom_on_rtss, self.layer_rtss.crs(), self.layer_ecusson.crs())
                if not self.layer_ecusson.isEditable(): self.layer_ecusson.startEditing()
                self.layer_ecusson.addFeature(QgsVectorLayerUtils.createFeature(self.layer_ecusson, geom_on_rtss, att))
                self.canvas.refresh()
    
    """
    Méthode activé quand le curseur se déplace dans la carte
    Entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur
                                dans la carte
    """
    def canvasMoveEvent(self, e):
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        # Get infos du RTSS le plus proche du cursor
        point_on_rtss, num_rtss, chainage, dist = self.geocode.getPointOnRTSS(geom)
        point_on_rtss = point_on_rtss.asPoint()
        # Vérifier si le curseur est dans la distance de tolérance de QGIS avec le RTSS
        if dist <= self.canvas.scale() * (self.searchRadiusMM()/1000):
            # Projeter le point sur le RTSS dans la projection de la carte
            if self.layer_rtss.crs() != QgsProject.instance().crs(): point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss)
            self.rtss_marker.setCenter(point_on_rtss)
            # Afficher le le marker de RTSS dans la carte
            self.rtss_marker.show()
        # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
        else: self.rtss_marker.hide()
    
    """ Méthode appelée quand l'outil est désactivé """
    def deactivate(self):
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            try: self.layer_ecusson.willBeDeleted.disconnect(self.deactivate)
            except: pass
            self.canvas.scene().removeItem(self.rtss_marker)
            # Désactiver l'outil
            self.canvas.unsetMapTool(self)
            QgsMapTool.deactivate(self)

pass
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        