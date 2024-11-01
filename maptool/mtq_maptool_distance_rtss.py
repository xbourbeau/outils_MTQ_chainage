# -*- coding: utf-8 -*-

from qgis.core import QgsGeometry, QgsApplication
from qgis.gui import QgsMapToolEmitPoint, QgsMapTool, QgsMapCanvas, QgsVertexMarker
from qgis.PyQt.QtWidgets import QMenu

from ..mtq.geomapping.imports import Geocodage, Chainage, LineRTSS, FeatRTSS
from ..modules.PluginParametres import PluginParametres
from ..modules.TemporaryGeometry import TemporaryGeometry

# DEV: Ajouter la possiblilité d'enregistrer la mesure dans une couches?

class MtqMapToolLongueurRTSS(QgsMapToolEmitPoint):

    def __init__(self, canvas:QgsMapCanvas, geocode:Geocodage, txt_distance):
        # Class de géocodage
        self.geocode = geocode
        self.txt_distance = txt_distance
        self.layer_rtss = None
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.mCursor = QgsApplication.getThemeCursor(3)
        # Class qui gère l'enregistrement des paramètres
        self.params = PluginParametres()
    
    def reset(self):
        """ Réinitialiser l'outil """
        # Reset la géometrie du segment temporaire
        self.segment_temporaire.reset()
        # Cacher l'indicateur de RTSS
        self.rtss_marker.hide()
        self.extremetie_marker_1.hide()
        self.extremetie_marker_2.hide()
        # Arrêter le tracage de l'outils
        self.is_tracing = False
        # Reset les valeurs du segment
        self.mesure_line = LineRTSS()
        # Reset le lable de distance 
        self.showDistance()
    
    def activate(self):
        """ Méthode appelée quand l'outil est activé """
        # Définir le cursor à utiliser
        self.canvas().setCursor(self.mCursor)
        self.canvas().scaleChanged.connect(self.updateTolerance)
        self.updateTolerance(self.canvas().scale())
        # Geometry temporaire (segment)
        self.segment_temporaire = TemporaryGeometry.createGeometryDistance(self.canvas())
        # Geometry temporaire de la position sur le RTSS
        self.rtss_marker = TemporaryGeometry.createMarkerDistanceSnap(self.canvas())
        
        self.extremetie_marker_1 = TemporaryGeometry.createMarkerDistanceExt(self.canvas())
        self.extremetie_marker_2 = TemporaryGeometry.createMarkerDistanceExt(self.canvas())
        self.reset()
    
    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)
    
    def canvasPressEvent(self, e):
        """
        Méthode activé quand la carte est cliquée

        Args:
            - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
        """
        # Click Gauche    
        if e.button() == 1:
            # Créer une nouvelle géometries
            if self.is_tracing:
                # Afficher la distance
                self.showDistance()
                # Arrêter de tracé
                self.is_tracing = False
            # Premier point du traçage
            else:
                # Reset pour s'il y avait déjà une distance 
                self.reset()
                self.extremetie_marker_1.setCenter(self.rtss_marker.center())
                self.extremetie_marker_1.show()
                # Geometrie du point dans la projection de la couche des RTSS
                geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
                # Liste des 5 RTSS les plus proche du click avec une fistance de recherche(m) selon le paramètre de QGIS 
                list_feat_rtss = self.geocode.nearestsRTSS(geom, 5, self.tolerance)
                # Choisir le RTSS à utiliser
                if len(list_feat_rtss) == 1: feat_rtss = list_feat_rtss[0]
                # Demander à l'utilisateur de choisir via un menu
                elif len(list_feat_rtss) > 1: feat_rtss = self.showMenuChoix(list_feat_rtss, e.globalPos())
                # Aucun RTSS à proximité
                else: feat_rtss = None
                if feat_rtss is None: return None
                # Commencer le tracage
                self.is_tracing = True
                # le featRTSS le plus proche du click de la souris
                self.feat_rtss = feat_rtss
                # Chainage du premier point de la mesure
                point_rtss = self.feat_rtss.geocoderInversePoint(geom)
                self.mesure_line.setPoints([point_rtss, point_rtss])
                
        # Click Droit
        else: self.reset()
    
    def canvasMoveEvent(self, e):
        """
        Méthode activé quand le curseur se déplace dans la carte

        Args:
            - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur dans la carte
        """
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        # Vérifier si une mesure est en train d'être prise
        if self.is_tracing:
            # Le chainage du point sur le RTSS le plus proche de la souris
            self.mesure_line.setEnd(self.feat_rtss.geocoderInversePoint(geom))
            # Si les chainages sont differents
            if self.mesure_line.isValide():
                geom_line_mesure = self.feat_rtss.geocoderLine(self.mesure_line, on_rtss=True)
                self.segment_temporaire.setToGeometry(geom_line_mesure, self.layer_rtss.crs())
                self.extremetie_marker_2.setCenter(geom_line_mesure.asPolyline()[-1])
                self.extremetie_marker_2.show()
                
            # Montrer la distance
            self.showDistance()
        # Aucune mesure est en train d'être prise
        else:
            # Get infos du RTSS le plus proche du cursor
            point_on_rtss = self.geocode.geocoderPointOnRTSS(geom, dist_max=self.tolerance)
            # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
            if point_on_rtss is None : return self.rtss_marker.hide()
            
            # Projeter le point sur le RTSS dans la projection de la carte
            point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss.getGeometry().asPoint())
            self.rtss_marker.setCenter(point_on_rtss)
            # Afficher le le marker de RTSS dans la carte
            self.rtss_marker.show()

    def updateTolerance(self, scale):
        """ Méthode qui permet de mettre à jour la tolérance de snapage """
        self.tolerance = scale * (self.searchRadiusMM()/1000)

    def flashGeometry(self, action):
        # Vérifier si l'entité ne vient pas d'être flashé 
        if action.text() != self.last_flash:
            # Garder en mémoire l'entité qui vient d'être flashé 
            self.last_flash = action.text()
            # Flasher la géometrie du RTSS survolé dans le menu
            self.canvas().flashGeometries([self.geocode.get(action.text()).geometry()], self.layer_rtss.crs(), flashes=1, duration=200)
    
    def showMenuChoix(self, list_rtss:list[FeatRTSS], pos):
        # Instance de menu
        menu = QMenu() 
        # Faire clignoter la géometrie du RTSS dont la souris est par dessus dans le menu
        menu.hovered.connect(self.flashGeometry)
        # Parcourir les choix pour les ajouter au menu
        self.last_flash = None
        # Ajouter les options au menu
        for rtss in list_rtss: menu.addAction(rtss.valueFormater())
        # Montrer le menu 
        choix_utilisateur = menu.exec_(pos)
        # Lorsque le choix est fait, déconnecter la méthode du menu
        menu.hovered.disconnect(self.flashGeometry)
        # Retourner le choix du RTSS, si un choix à été fait
        return None if choix_utilisateur is None else self.geocode.get(choix_utilisateur.text())
    
    def showDistance(self):
        # Distance entre le point 1 et 2
        dist_chainage = self.mesure_line.length()
        precision = self.params.getValue("precision_mesure")
        # Formater et arrondire
        if self.params.getValue("formater_chainage"):
            dist_chainage = Chainage(dist_chainage).valueFormater(precision)
        else: 
            # Définir le format en fonction de la précision
            number_format = '{:.%if}' % (precision if precision >= 0 else 0)
            dist_chainage = number_format.format(round(dist_chainage, precision))
        # Afficher la distance
        self.txt_distance.setText(dist_chainage)
        
    def deactivate(self):
        """ Méthode appelée quand l'outil est désactivé """
        if self.isActive():
            self.canvas().scaleChanged.disconnect(self.updateTolerance)
            # Retirer de la carte les géometries créées
            self.canvas().scene().removeItem(self.segment_temporaire)
            self.canvas().scene().removeItem(self.rtss_marker)
            self.canvas().scene().removeItem(self.extremetie_marker_1)
            self.canvas().scene().removeItem(self.extremetie_marker_2)
            self.canvas().unsetMapTool(self)
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            # Désactiver l'outil
            QgsMapTool.deactivate(self)
