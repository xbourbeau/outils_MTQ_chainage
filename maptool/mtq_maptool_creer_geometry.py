# -*- coding: utf-8 -*-
from qgis.core import (QgsGeometry, QgsApplication, QgsProject, QgsFeature, QgsTolerance,
    QgsWkbTypes, Qgis, QgsVectorLayerUtils, QgsPointXY, QgsSnappingUtils, QgsSnappingConfig,
    QgsPointLocator)
from qgis.gui import (QgsMapTool, QgsMapToolEdit, QgisInterface, QgsVertexMarker,
    QgsMapCanvas, QgsAttributeEditorContext, QgsMapCanvasSnappingUtils)
from PyQt5.QtCore import Qt
from qgis.PyQt.QtWidgets import QMenu
from qgis.PyQt.QtGui import QKeySequence

from ..modules.PluginParametres import PluginParametres
from ..modules.TemporaryGeometry import TemporaryGeometry

from ..interfaces.fenetre_create_geometry import fenetreCreationGeometrie

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

        #self.dlg_geom = fenetreCreationGeometrie(self.iface, self.geocode)
        #self.dlg_geom.spx_chainage.valueChanged.connect(self.updateChainage)
        #self.dlg_geom.spx_offset.valueChanged.connect(self.updateOffset)
        #self.dlg_geom.set_lock_chainage.connect(self.lockSnapPerpendicularlLine)
        #self.dlg_geom.set_lock_offset.connect(self.lockSnapParralelLine)

        #self.dlg_geom.btn_add.clicked.connect(self.addPoint)

        # Définition du curseur
        self.mCursor = QgsApplication.getThemeCursor(4)
        self.layer_rtss = None
        self.snapping_utils = QgsMapCanvasSnappingUtils(self.canvas())

    def activate(self):
        # Définir les variables utilisé pour le snap parralèl
        self.show_parralel_snap, self.snap_offset = False, 0
        # Définir les variables utilisé pour le snap perpendiculaire
        self.show_perpendicular_snap, self.snap_chainage = False, 0
        # Activer le curseur
        self.canvas().setCursor(self.mCursor)

        # Ajouter un élément de text à la carte pour afficher les mesures 
        self.info_text = self.canvas().scene().addText("")
        self.info_text.hide()
        # Définir la police du tooltip a affihcer sur la carte
        self.info_text.setFont(self.params.getValue("font_on_map"))
        self.html_tooltip = '<p style="color:%s"><i>{}</i></p>' % self.params.getValue("color_font_on_map")

        # Cérer les géometries temporaires du maptool
        self.new_point_marker = TemporaryGeometry.createMarkerNewPoint(self.canvas())
        
        self.new_geom = TemporaryGeometry.createNewGeom(self.canvas())
        self.new_geom_prolg = TemporaryGeometry.createNewGeomProlongation(self.canvas())

        self.snap_line_parralel = TemporaryGeometry.createSnappingLine(self.canvas())
        self.snap_line_perpendiculair = TemporaryGeometry.createSnappingLine(self.canvas())

        self.snap_marker = TemporaryGeometry.createMarkerSnap(self.canvas())
        self.snap_intersect_marker = TemporaryGeometry.createIntersectionMarkerSnap(self.canvas())

        self.iface.currentLayerChanged.connect(self.setActiveLayer)
        self.setActiveLayer()

        self.snapping_utils.setConfig(QgsProject.instance().snappingConfig())
        QgsProject.instance().snappingConfigChanged.connect(lambda: self.snapping_utils.setConfig(QgsProject.instance().snappingConfig()))
        #self.dlg_geom.setInterfaceActive()

        self.reset()
    
    def reset(self):
        """ Réinitialiser l'outil """
        # Cacher les géometries temporaire
        self.new_geom.hide()
        self.new_geom_prolg.hide()
        self.new_point_marker.hide()
        self.info_text.hide()
        self.snap_marker.hide()
        self.snap_intersect_marker.hide()
        self.previous_pt_rtss = None
        self.stop_moving = False
        self.list_points = []
        self.line_rtss = LineRTSS([])
        self.polygon_rtss = PolygonRTSS([])
        self.new_geom.setToGeometry(QgsGeometry())

        self.feat_rtss = None
        self.check_rtss = False
        self.current_pt_rtss = None

    def setActiveLayer(self):
        self.active_layer = self.currentVectorLayer()
        try: self.geom_type = self.active_layer.geometryType()
        except: self.geom_type = -1
        self.reset()

    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)

    def getSnappedPoint(self, e):
        """ Obtenir le point de snap """
        # Effectuer le snap avec la position de la souris
        snap_match = self.snapping_utils.snapToMap(e.pos())
        # Indicateur pour savoir si le snap est sur un RTSS
        self.check_rtss = False

        # Vérifier si le snap est valide (trouvée un résultat)
        if snap_match.isValid():
            # Définir le type de snap
            type_snap = snap_match.type()
            # Indicatueur pour savoir si le snap est une intersection
            use_intersection = False
            # Vérifier le type de snap pour définir le synmbole du marker
            if type_snap == QgsPointLocator.Vertex: 
                # Check intesection in a weird way 
                use_intersection = snap_match.featureId() == 0
                self.snap_marker.setIconType(QgsVertexMarker.ICON_BOX)

            elif type_snap == QgsPointLocator.Edge: self.snap_marker.setIconType(QgsVertexMarker.ICON_X)
            elif type_snap == QgsPointLocator.Centroid: self.snap_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            else: self.snap_marker.setIconType(QgsVertexMarker.ICON_BOX)

            # Vérifier si le snap est sur un RTSS
            if snap_match.layer() == self.layer_rtss: self.check_rtss = True

            # Vérifier si le snap est une intersection
            if use_intersection:
                # Définir le snap marker à l'intersection
                self.snap_intersect_marker.setCenter(snap_match.point())
                self.snap_intersect_marker.show()
                self.snap_marker.hide()
            # Sinon afficher le marker de snap normal
            else:
                self.snap_marker.setCenter(snap_match.point())
                self.snap_marker.show()
                self.snap_intersect_marker.hide()
            # Retourner le point de snap
            return snap_match.point()
        
        # Sinon cacher les markers de snap
        self.snap_intersect_marker.hide()
        self.snap_marker.hide()
        # Retourner la position du curseur
        return self.toLayerCoordinates(self.layer_rtss, e.pos())

    def canvasPressEvent(self, e):
        """
        Méthode activé quand la carte est cliquée

        Args:
            - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
        """
        if self.active_layer == 0: return None
        if not self.active_layer.isEditable(): return None
        # Click Gauche    
        if e.button() == 1: self.addPoint()
        # Click Droit
        else: 
            if self.geom_type == 1 or self.geom_type == 2:
                geom = self.new_geom.asGeometry()
                if not geom.isEmpty():
                    geom = reprojectGeometry(geom, QgsProject.instance().crs(), self.active_layer.crs())
                    self.stop_moving = True
                    if geom.isGeosValid(): return self.createNewFeature(geom)
            self.reset()
    
    def canvasMoveEvent(self, e):
        """
        Méthode activé quand le curseur se déplace dans la carte

        Args:
            - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur dans la carte
        """
        # Rien faire
        if self.stop_moving: return None

        point = self.getSnappedPoint(e)
        
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(point)
        # Get infos du RTSS le plus proche du cursor
        if self.feat_rtss: self.current_pt_rtss = self.feat_rtss.geocoderInversePoint(geom)
        else: 
            # Si le snap est fait sur un RTSS, utilisé celui le plus proche du cursor
            if self.check_rtss: 
                feat_rtss = self.geocode.nearestRTSSFromPoint(QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos())))
                self.current_pt_rtss = feat_rtss.geocoderInversePoint(geom)
            # Sinon, utilisé le RTSS le plus proche du point snapper
            else: self.current_pt_rtss = self.geocode.geocoderInversePoint(geom)
        # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
        if self.current_pt_rtss is None : return self.new_point_marker.hide()
        self.setPoint()

        # Ajouter le text qui indique la largeur et hauteur d'un polygone
        if self.current_pt_rtss and self.previous_pt_rtss:
            # Calculer la différence des offsets entre le dernier point et le prochain
            offset = abs(self.previous_pt_rtss.getOffset() - self.current_pt_rtss.getOffset())
            # Calculer la différence des chainages entre le dernier point et le prochain
            long = self.previous_pt_rtss.getChainage() - self.current_pt_rtss.getChainage()
            long = abs(long.value())

            # Affichier le text de la différence la plus élever entre le offset et le chainage
            if offset >= long: self.info_text.setHtml(self.html_tooltip.format(f"O: {offset:.1f}"))
            else: self.info_text.setHtml(self.html_tooltip.format(f"L: {long:.1f}"))

            # Créer une ligne entre les 2 points et conserver seulment la partie visible
            last_line = LineRTSS([self.previous_pt_rtss, self.current_pt_rtss])
            if last_line.isValide():
                last_line = self.feat_rtss.geocoderLine(last_line).clipped(self.canvas().extent())
                if last_line:
                    # Définir le point central de la ligne
                    point = self.toCanvasCoordinates(last_line.interpolate(last_line.length()/2).asPoint())
                    # Placer le text avec le point
                    self.info_text.setPos(point.x(), point.y())
                    self.info_text.show()

    def addPoint(self):
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

    def setPoint(self, update_window=True):
        self.setSnapParralelLine()
        self.setSnapPerpendicularlLine()
        
        if self.geom_type == 0:
            point_geom = self.geocode.geocoderPoint(self.current_pt_rtss)
            # Projeter le point sur le RTSS dans la projection de la carte
            point_geom = self.toMapCoordinates(self.layer_rtss, point_geom.asPoint())
            self.new_point_marker.setCenter(point_geom)
            # Afficher le le marker de RTSS dans la carte
            self.new_point_marker.show()
            #self.dlg_geom.setValuesFromPoint(self.current_pt_rtss, is_signal=not update_window)

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
                #self.dlg_geom.setValuesFromPoint(self.current_pt_rtss, is_signal=not update_window)
            else: self.new_geom_prolg.hide()

    def updateChainage(self, chainage):
        self.current_pt_rtss.setChainage(chainage)
        self.setPoint(update_window=False)

    def updateOffset(self, offset):
        self.current_pt_rtss.setOffset(offset)
        self.setPoint(update_window=False)

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
        new_feat = QgsVectorLayerUtils.createFeature(self.active_layer, geom, {})

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
            if self.show_perpendicular_snap: self.lockSnapPerpendicularlLine()
            #self.dlg_geom.lockOffset(True)
        else:
            self.snap_line_parralel.hide()
            #self.dlg_geom.lockOffset(False)

    def setSnapPerpendicularlLine(self):
        if self.show_perpendicular_snap:
            length = self.canvas().extent().perimeter()/4
            feat_rtss = self.geocode.get(self.current_pt_rtss.getRTSS())
            self.current_pt_rtss.setChainage(self.snap_chainage)
            line_geom = feat_rtss.getTransect(chainage=self.snap_chainage, dist_d=length, dist_g=length)
            self.snap_line_perpendiculair.setToGeometry(line_geom)
            self.snap_line_perpendiculair.show()
            if self.show_parralel_snap: self.lockSnapParralelLine()
            #self.dlg_geom.lockChainage(True)
        else:
            self.snap_line_perpendiculair.hide()
            #self.dlg_geom.lockChainage(False)

    def keyPressEvent(self, e):
        key = QKeySequence(e.key())
        # Vérifier le raccourci clavier pour le snap parralele 
        if self.params.getKeySequence("raccourcis_clavier_parralele").matches(key) == 2: self.lockSnapParralelLine()
        # Vérifier le raccourci clavier pour le snap perpendiculaire
        if self.params.getKeySequence("raccourcis_clavier_perpendiculaire").matches(key) == 2: self.lockSnapPerpendicularlLine()

    def lockSnapParralelLine(self):
        self.show_parralel_snap = not self.show_parralel_snap
        if self.previous_pt_rtss: self.snap_offset = self.previous_pt_rtss.getOffset()
        else: self.snap_offset = self.current_pt_rtss.getOffset()
        self.setSnapParralelLine()

    def lockSnapPerpendicularlLine(self):
        self.show_perpendicular_snap = not self.show_perpendicular_snap
        if self.previous_pt_rtss: self.snap_chainage = self.previous_pt_rtss.getChainage()
        else: self.snap_chainage = self.current_pt_rtss.getChainage()
        self.setSnapPerpendicularlLine()

    def deactivate(self):
        if self.isActive():
            #self.dlg_geom.close()
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            # Retirer de la carte les géometries créées
            self.canvas().scene().removeItem(self.snap_line_perpendiculair)
            self.canvas().scene().removeItem(self.snap_line_parralel)
            self.canvas().scene().removeItem(self.snap_marker)
            self.canvas().scene().removeItem(self.new_point_marker)
            self.canvas().scene().removeItem(self.new_geom_prolg)
            self.canvas().scene().removeItem(self.new_geom)
            self.canvas().scene().removeItem(self.info_text)
            self.canvas().scene().removeItem(self.snap_intersect_marker)

            self.iface.currentLayerChanged.disconnect(self.setActiveLayer)

            self.canvas().unsetMapTool(self)
            # Désactiver l'outil
            QgsMapTool.deactivate(self)    

