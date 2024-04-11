# -*- coding: utf-8 -*-
import os

from qgis.core import QgsProject, QgsGeometry, QgsVectorLayerUtils, QgsCoordinateTransform, QgsField, QgsVectorLayer, QgsExpressionContextUtils
from qgis.gui import QgsMapToolEdit, QgsVertexMarker, QgsMapTool
from PyQt5.QtCore import Qt, QPoint
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMenu
from qgis.PyQt.QtCore import QVariant

from ..gestion_parametres import sourceParametre
from ..mtq.fnt import reprojectFeat, validateLayer
from ..functions.addLayerToMap import addLayerToMap

'''
========================= Outil Tracer un segment parallel =======================================
'''
class MtqMapToolNewEcusson(QgsMapToolEdit):
    
    def __init__(self, canvas, layer_rtss, geocode):
        # Reference de la carte
        self.canvas = canvas
        # Class de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = layer_rtss
        # Le QgsMapTool actif dans la carte avant cette outils
        self.last_maptool = None
        
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapToolEdit.__init__(self, self.canvas)
        
        # Class qui gère l'enregistrement des paramètres
        self.gestion_parametre = sourceParametre()
          
        # Geometry temporaire de la position sur le RTSS
        self.rtss_marker = QgsVertexMarker(self.canvas)
        self.rtss_marker.setColor(QColor("#178e0c"))
        self.rtss_marker.setIconSize(10)
        self.rtss_marker.setIconType(QgsVertexMarker.ICON_X)
        self.rtss_marker.setPenWidth(3)
    
    ''' Réinitialiser l'outil '''
    def reset(self):
        # Cacher l'indicateur de RTSS
        self.rtss_marker.hide()
        # Arrêter le tracage de l'outils
        self.is_tracing = False
    
    def setLayerEcusson(self, layer):
        self.layer_ecusson = layer
    
    '''
    Méthode appelée quand l'outil est activé
    '''
    def activate(self):
        # Définir le cursor à utiliser
        self.canvas.setCursor(self.mCursor)
        # Ajouter à la carte les géometries temporaire
        self.canvas.scene().addItem(self.rtss_marker)
        
        #layer_name = self.gestion_parametre.getParam("layer_ecusson_name").getValue()
        field_name = self.gestion_parametre.getParam("layer_ecusson_field_route").getValue()
        field_name_classe = self.gestion_parametre.getParam("layer_ecusson_field_classe").getValue()
        #self.layer_ecusson = validateLayer(layer_name, fields_name=[field_name], geom_type=0)
        #if not self.layer_ecusson:
        #    self.layer_ecusson = self.createNewLayer()
        #    path_to_ecusson = os.path.join(self.gestion_parametre.getParam("ecusson_path").getValue(), "styles")
        #    QgsExpressionContextUtils.setLayerVariable(self.layer_ecusson, 'path_to_ecusson', path_to_ecusson)
        
        # Rendre la couche en édition
        if not self.layer_ecusson.isEditable(): self.layer_ecusson.startEditing()
        # Référence de la couche des écussons
        self.field_index = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name]
        if self.field_index: self.field_index = self.field_index[0]
        else: self.field_index = 0
        
        self.field_index_classe = [i for i, field in enumerate(self.layer_ecusson.fields()) if field.name() == field_name_classe]
        if self.field_index_classe: self.field_index_classe = self.field_index_classe[0]
        else: self.field_index_classe = None
        
        self.layer_ecusson.willBeDeleted.connect(self.deactivate)
        
        self.reproject_feat = self.layer_ecusson.crs() != self.layer_rtss.crs()
        self.trasform = QgsCoordinateTransform(self.layer_rtss.crs(), self.layer_ecusson.crs(), QgsProject.instance())
        
        self.reset()
    
    ''' Function pour definir un QgsMapTool à rendre actif lorsque celui-ci est désactivé. '''
    def lastMapTool(self, maptool):
        # Garder en mémoire le QgsMapTool à rendre actif lors de la désactivation
        self.last_maptool = maptool
    
    def createNewLayer(self):
        # Create layer
        layer_ecusson = QgsVectorLayer(f"point?crs={self.layer_rtss.crs().authid()}", self.gestion_parametre.getParam("layer_ecusson_name").getValue(), "memory")
        # Add fields
        field_route = self.gestion_parametre.getParam("layer_ecusson_field_route").getValue()
        field_class = self.gestion_parametre.getParam("layer_ecusson_field_classe").getValue()
        if field_route == '': field_route = "num_route"
        if field_class == field_route: field_class = "Classification"
        if field_class == '': field_class = "Classification"
        layer_ecusson.dataProvider().addAttributes([ QgsField(field_route, QVariant.String), QgsField(field_class, QVariant.String)])
        layer_ecusson.updateFields()
        return addLayerToMap(self.canvas, layer_ecusson, style=self.gestion_parametre.getParam("layer_ecusson_style").getValue())
        
    '''
    Méthode activé quand la carte est cliquée
    Paramètre entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
    '''
    def canvasPressEvent(self, e):
        # Click Gauche    
        if e.button() == 1:
            # Geometrie du point dans la projection de la couche des RTSS
            geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
            # Get infos du RTSS le plus proche du cursor
            geom_on_rtss, num_rtss, chainage, dist = self.geocode.getPointOnRTSS(geom)
            point_on_rtss = geom_on_rtss.asPoint()
            # Distance de recherche(m) selon le paramètre de QGIS 
            search_dist = self.canvas.scale() * (self.searchRadiusMM()/1000)
            # Vérifier si le curseur est dans la distance de tolérance de QGIS avec le RTSS
            if dist <= search_dist:
                # Placer le marker sur le point du RTSS 
                if self.layer_rtss.crs() != QgsProject.instance().crs():
                    # Projeter le point sur le RTSS dans la projection de la carte
                    point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss)
                self.rtss_marker.setCenter(point_on_rtss)
                num_route = str(int(num_rtss[:5]))
                att = {self.field_index: num_route}
                # Ajouter la classification fonctionnelle si possible
                if self.field_index_classe:
                    feats = [feat for feat in self.layer_rtss.getFeatures(f"\"{self.gestion_parametre.getParam('field_num_rtss').getValue()}\" = '{num_rtss}'")]
                    if feats: classification = feats[0][self.gestion_parametre.getParam('field_classification').getValue()]
                    else: classification = '00'
                    att[self.field_index_classe] = classification
                # Reprojeter la géometrie du point de l'écusson si besoin
                if self.reproject_feat: geom_on_rtss.transform(self.trasform)
                new_feat = QgsVectorLayerUtils.createFeature(self.layer_ecusson, geom_on_rtss, att)
                self.layer_ecusson.addFeature(new_feat)
                self.canvas.refresh()
                
        # Click Droit
        else: self.deactivate()
    
    '''
    Méthode activé quand le curseur se déplace dans la carte
    Entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur
                                dans la carte
    '''
    def canvasMoveEvent(self, e):
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        
        # Get infos du RTSS le plus proche du cursor
        point_on_rtss, num_rtss, chainage, dist = self.geocode.getPointOnRTSS(geom)
        point_on_rtss = point_on_rtss.asPoint()
        # Distance de recherche(m) selon le paramètre de QGIS 
        search_dist = self.canvas.scale() * (self.searchRadiusMM()/1000)
        # Vérifier si le curseur est dans la distance de tolérance de QGIS avec le RTSS
        if dist <= search_dist:
            # Placer le marker sur le point du RTSS 
            if self.layer_rtss.crs() != QgsProject.instance().crs():
                # Projeter le point sur le RTSS dans la projection de la carte
                point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss)
            self.rtss_marker.setCenter(point_on_rtss)
            # Afficher le le marker de RTSS dans la carte
            self.rtss_marker.show()
        else:
            # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
            self.rtss_marker.hide()
    
    '''
        Méthode appelée quand l'outil est désactivé
    '''
    def deactivate(self):
        # Émettre le signal de desactivation de l'outil
        self.deactivated.emit()
        
        try: self.layer_ecusson.willBeDeleted.disconnect(self.deactivate)
        except: pass
        self.canvas.scene().removeItem(self.rtss_marker)
        
        # Désactiver l'outil
        self.canvas.unsetMapTool(self)
        QgsMapTool.deactivate(self)
        # Essayer de remettre le dernier QgsMapTool actif
        if self.last_maptool: self.canvas.setMapTool(self.last_maptool)
        self.last_maptool = None

pass
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        