# -*- coding: utf-8 -*-
from qgis.core import QgsVectorLayerUtils, QgsApplication
from qgis.gui import QgsMapTool, QgisInterface

from ..mtq.core import Geocodage
from ..mtq.utils import Utilitaire
from ..mtq.fnt import reprojectGeometry

from ..modules.PluginParametres import PluginParametres
from ..modules.TemporaryGeometry import TemporaryGeometry
from ..modules.PluginTemporaryLayer import PluginTemporaryLayer

class MtqMapToolNewEcusson(QgsMapTool):
    """ Outil qui permet d'ajouter des points réprésentant des éccussons à une couche """
    
    def __init__(self, iface:QgisInterface, geocode:Geocodage):
        # Class de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = None
        self.iface = iface
        self.first_message = True
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapTool.__init__(self, self.iface.mapCanvas())
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
        
        # Définir la couche des écussons à utiliser
        self.layer_ecusson = PluginTemporaryLayer.getLayerEcusson(self.canvas(), self.layer_rtss.crs().authid())
        # Définir l'index de ses champs
        self.setFieldsIndex()

        # Suivre si la couche vas être supprimer 
        self.layer_ecusson.willBeDeleted.connect(self.deactivate)
        self.canvas().scaleChanged.connect(self.updateTolerance)

        self.updateTolerance(self.canvas().scale())
    
    def setFieldsIndex(self):
        """ Permet de définir l'index des champs spécifé de la couche des éccussons """
        # Champs à connaitre les index
        field_name = self.params.getValue("layer_ecusson_field_route")
        field_name_classe = self.params.getValue("layer_ecusson_field_classe")
        
        # Définir l'index du champs des numéros de routes 
        self.field_index = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name]
        if self.field_index: self.field_index = self.field_index[0]
        else: self.field_index = 0

        # Définir l'index du champs de classification fonctionnelle
        self.field_index_classe = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name_classe]
        if self.field_index_classe: self.field_index_classe = self.field_index_classe[0]
        else: self.field_index_classe = None 
        
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
                # Avertir l'utilisateur qu'il n'y a pas de champs de classification fonctionnelle
                elif self.first_message:
                    self.first_message = False
                    Utilitaire.warningMessage(self.iface, "Aucun champ de classification fonctionnelle n'est défini pour le type d'écusson")
                
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
    
        