# -*- coding: utf-8 -*-
from qgis.core import (QgsGeometry, QgsVectorLayerUtils, 
    QgsField, QgsVectorLayer, QgsExpressionContextUtils, QgsApplication)
from qgis.gui import QgsMapTool, QgsMapCanvas
from qgis.PyQt.QtCore import QVariant

from ..mtq.core import Geocodage
from ..mtq.functions import reprojectGeometry, validateLayer
from ..modules.PluginParametres import PluginParametres
from ..functions.addLayerToMap import addLayerToMap
from ..modules.TemporaryGeometry import TemporaryGeometry

class MtqMapToolNewEcusson(QgsMapTool):
    """ Outil qui permet d'ajouter des points réprésentant des éccussons à une couche """
    
    def __init__(self, canvas:QgsMapCanvas, geocode:Geocodage):
        # Class de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = None
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapTool.__init__(self, canvas)
        self.mCursor = QgsApplication.getThemeCursor(3)
        # Class qui gère l'enregistrement des paramètres
        self.params = PluginParametres()
    
    def setLayer(self, layer_id):
        """ Méthode qui permet de définir la couche des RTSS """
        self.layer_rtss = self.layer(layer_id)
    
    def activate(self):
        """ Méthode appelée quand l'outil est activé """
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
        # Geometry temporaire de la position sur le RTSS
        self.rtss_marker = TemporaryGeometry.createMarkerEcusson(self.canvas())
        
        field_name = self.params.getValue("layer_ecusson_field_route")
        field_name_classe = self.params.getValue("layer_ecusson_field_classe")
        
        self.layer_ecusson = validateLayer(self.params.getValue("layer_ecusson_name"), fields_name=[field_name], geom_type=0)
        if not self.layer_ecusson:
            self.layer_ecusson = self.createNewLayer()
            path_to_ecusson = self.params.getValue("ecusson_path")
            QgsExpressionContextUtils.setLayerVariable(self.layer_ecusson, 'path_to_ecusson', path_to_ecusson)
        
        self.field_index = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name]
        if self.field_index: self.field_index = self.field_index[0]
        else: self.field_index = 0
        
        self.field_index_classe = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name_classe]
        if self.field_index_classe: self.field_index_classe = self.field_index_classe[0]
        else: self.field_index_classe = None
        
        self.layer_ecusson.willBeDeleted.connect(self.deactivate)
        self.canvas().scaleChanged.connect(self.updateTolerance)
        self.updateTolerance(self.canvas().scale())
    
    def createNewLayer(self):
        # Create layer
        layer_ecusson = QgsVectorLayer(
            f"point?crs={self.layer_rtss.crs().authid()}",
            self.params.getValue("layer_ecusson_name"),
            "memory")
        # Add fields
        field_route = self.params.getValue("layer_ecusson_field_route")
        field_class = self.params.getValue("layer_ecusson_field_classe")
        if field_route == '': field_route = "num_route"
        if field_class == field_route or field_class == '': field_class = "Classification"
        layer_ecusson.dataProvider().addAttributes([
            QgsField(field_route, QVariant.String),
            QgsField(field_class, QVariant.String)])
        layer_ecusson.updateFields()
        return addLayerToMap(self.canvas(), layer_ecusson, style=self.params.getValue("layer_ecusson_style"))
        
    def canvasPressEvent(self, e):
        """
        Méthode activé quand la carte est cliquée
        Paramètre entrée:
            - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
        """
        # Click Gauche    
        if e.button() == 1:
            # Geometrie du point dans la projection de la couche des RTSS
            geom = self.toLayerCoordinates(self.layer_rtss, e.pos())
            # Get infos du RTSS le plus proche du cursor
            point_on_rtss = self.geocode.geocoderPointOnRTSS(geom, dist_max=self.tolerance)
            if point_on_rtss is not None:
                att = {self.field_index: point_on_rtss.getRTSS().getRoute(zero=False)}
                # Ajouter la classification fonctionnelle si possible
                if point_on_rtss.getRTSS().hasAttribut("class_fonct") and self.field_index_classe:
                    att[self.field_index_classe] = str(point_on_rtss.getRTSS().getAttribut("class_fonct"))
                point_on_rtss = reprojectGeometry(point_on_rtss.getGeometry(), self.layer_rtss.crs(), self.layer_ecusson.crs())
                if not self.layer_ecusson.isEditable(): self.layer_ecusson.startEditing()
                self.layer_ecusson.addFeature(QgsVectorLayerUtils.createFeature(self.layer_ecusson, point_on_rtss, att))
                self.canvas().refresh()
    
    def canvasMoveEvent(self, e):
        """
        Méthode activé quand le curseur se déplace dans la carte
        Entrée:
            - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur
                                    dans la carte
        """
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = self.toLayerCoordinates(self.layer_rtss, e.pos())
        # Get infos du RTSS le plus proche du cursor
        point_on_rtss = self.geocode.geocoderPointOnRTSS(geom, dist_max=self.tolerance)
        # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
        if point_on_rtss is None : self.rtss_marker.hide()
        else:
            # Projeter le point sur le RTSS dans la projection de la carte
            point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss.getGeometry().asPoint())
            self.rtss_marker.setCenter(point_on_rtss)
            # Afficher le le marker de RTSS dans la carte
            self.rtss_marker.show()
    
    def updateTolerance(self, scale):
        """ Méthode qui permet de mettre à jour la tolérance de snapage """
        self.tolerance = scale * (self.searchRadiusMM()/1000)

    def deactivate(self):
        """ Méthode appelée quand l'outil est désactivé """
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            try: 
                self.canvas().scaleChanged.disconnect(self.updateTolerance)
                self.layer_ecusson.willBeDeleted.disconnect(self.deactivate)
            except: pass
            self.canvas().scene().removeItem(self.rtss_marker)
            # Désactiver l'outil
            self.canvas().unsetMapTool(self)
            QgsMapTool.deactivate(self)
    
        