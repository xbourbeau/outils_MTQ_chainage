# -*- coding: utf-8 -*-

from qgis.core import QgsProject, QgsGeometry, QgsApplication, QgsPointXY
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker, QgsMapTool
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMenu

from ..mtq.fnt import reprojectGeometry
from ..mtq.format import formaterChainage
from ..gestion_parametres import sourceParametre

"""
========================= Outil mesurer un segment d'un RTSS =======================================
"""
class MtqMapToolLongueurRTSS(QgsMapToolEmitPoint):
    
    #currentDistance = pyqtSignal(str)
    
    def __init__(self, canvas, geocode, txt_distance):
        # Reference de la carte
        self.canvas = canvas
        # Class de géocodage
        self.geocode = geocode
        self.txt_distance = txt_distance
        self.layer_rtss = None
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.mCursor = QgsApplication.getThemeCursor(3)
        # Class qui gère l'enregistrement des paramètres
        self.gestion_parametre = sourceParametre()
    
    """ Réinitialiser l'outil """
    def reset(self):
        # Reset la géometrie du segment temporaire
        self.segment_temporaire.reset()
        # Cacher l'indicateur de RTSS
        self.rtss_marker.hide()
        # Arrêter le tracage de l'outils
        self.is_tracing = False
        # Reset les valeurs du segment
        self.chainage_1, self.chainage_2 = 0, 0
        # Reset le lable de distance 
        self.showDistance()
    
    """ Méthode appelée quand l'outil est activé """
    def activate(self):
        # Définir le cursor à utiliser
        self.canvas.setCursor(self.mCursor)
        # Geometry temporaire (segment)
        self.segment_temporaire = QgsRubberBand(self.canvas)
        self.segment_temporaire.setColor(QColor("#e4741e"))
        self.segment_temporaire.setWidth(3)
        
        # Geometry temporaire de la position sur le RTSS
        self.rtss_marker = QgsVertexMarker(self.canvas)
        self.rtss_marker.setColor(QColor("#e4741e"))
        self.rtss_marker.setIconSize(9)
        self.rtss_marker.setIconType(QgsVertexMarker.ICON_X)
        self.rtss_marker.setPenWidth(3)
        self.reset()
    
    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)
    
    """
    Méthode activé quand la carte est cliquée
    Paramètre entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
    """
    def canvasPressEvent(self, e):
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
                # Geometrie du point dans la projection de la couche des RTSS
                geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
                # Liste des 5 RTSS les plus proche du click avec une fistance de recherche(m) selon le paramètre de QGIS 
                rtss_proche = self.geocode.nearestRTSS(geom, 5, self.canvas.scale() * (self.searchRadiusMM()/1000))
                # Choisir le RTSS à utiliser
                if len(rtss_proche) == 1: feat_rtss = rtss_proche[0]['rtss']
                # Demander à l'utilisateur de choisir via un menu
                elif len(rtss_proche) > 1: feat_rtss = self.showMenuChoix(rtss_proche, e.pos())
                # Aucun RTSS à proximité
                else: return None
                # Commencer le tracage
                self.is_tracing = True
                # le featRTSS le plus proche du click de la souris
                self.feat_rtss = feat_rtss
                # Chainage du premier point de la mesure
                self.chainage_1 = round(feat_rtss.getChainageFromPoint(geom), self.gestion_parametre.getParam("precision_chainage").getValue())
        # Click Droit
        else: self.reset()
    
    """
    Méthode activé quand le curseur se déplace dans la carte
    Entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur
                                dans la carte
    """
    def canvasMoveEvent(self, e):
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        #geom = reprojectGeometry(QgsGeometry.fromPointXY(QgsPointXY(e.pos().x(), e.pos().y())), QgsProject.instance().crs(), self.geocode.getCrs())
        
        # Vérifier si une mesure est en train d'être prise
        if self.is_tracing:
            # Le chainage du point sur le RTSS le plus proche de la souris
            self.chainage_2 = round(self.feat_rtss.getChainageFromPoint(geom), self.gestion_parametre.getParam("precision_chainage").getValue())
            # Si les chainages sont differents
            if self.chainage_1 != self.chainage_2:
                # Définir le chainage min et max
                chainage_d = min(self.chainage_1, self.chainage_2)
                chainage_f = max(self.chainage_1, self.chainage_2)
                self.segment_temporaire.setToGeometry(self.feat_rtss.getLineFromChainage(chainage_d, chainage_f), self.layer_rtss.crs())
            # Montrer la distance
            self.showDistance()
        # Aucune mesure est en train d'être prise
        else:
            # Get infos du RTSS le plus proche du cursor
            point_on_rtss, num_rtss, chainage, dist = self.geocode.getPointOnRTSS(geom)
            point_on_rtss = point_on_rtss.asPoint()
            # Distance de recherche(m) selon le paramètre de QGIS 
            search_dist = self.canvas.scale() * (self.searchRadiusMM()/1000)
            # Vérifier si le curseur est dans la distance de tolérance de QGIS avec le RTSS
            if dist <= search_dist:
                # Projeter le point sur le RTSS dans la projection de la carte
                if self.layer_rtss.crs() != QgsProject.instance().crs(): point_on_rtss = self.toMapCoordinates(self.layer_rtss, point_on_rtss)
                self.rtss_marker.setCenter(point_on_rtss)
                # Afficher le le marker de RTSS dans la carte
                self.rtss_marker.show()
            # Ne pas afficher le curseur s'il n'est pas assez proche d'un RTSS
            else: self.rtss_marker.hide()


    def flashGeometry(self, action):
        # Vérifier si l'entité ne vient pas d'être flashé 
        if action.text() != self.last_flash:
            # Garder en mémoire l'entité qui vient d'être flashé 
            self.last_flash = action.text()
            # Flasher la géometrie du RTSS survolé dans le menu
            self.canvas.flashGeometries([self.geocode.getRTSS(action.text()).getGeometry()], self.layer_rtss.crs(), flashes=1, duration=200)
    
    def showMenuChoix(self, list_rtss, point):
        # Instance de menu
        menu = QMenu() 
        # Faire clignoter la géometrie du RTSS dont la souris est par dessus dans le menu
        menu.hovered.connect(self.flashGeometry)
        # Parcourir les choix pour les ajouter au menu
        self.last_flash = None
        # Ajouter les options au menu
        for rtss in list_rtss: action = menu.addAction(rtss['rtss'].getRTSS(formater=True))
        # Montrer le menu 
        choix = menu.exec_(pos)
        # Lorsque le choix est fait, déconnecter la méthode du menu
        menu.hovered.disconnect(self.flashGeometry)
        # Retourner le choix du RTSS, si un choix à été fait
        return None if choix_utilisateur is None else self.geocode.getRTSS(choix_utilisateur.text())
    
    def showDistance(self):
        # Distance entre le point 1 et 2
        dist_chainage = abs(self.chainage_1 - self.chainage_2)
        precision = self.gestion_parametre.getParam("precision_chainage").getValue()
        # Formater et arrondire
        if self.gestion_parametre.getParam("formater_chainage").getValue(): dist_chainage = formaterChainage(dist_chainage, precision)
        else: 
            # Définir le format en fonction de la précision
            if precision < 0: number_format = '{:.%if}' % (precision)
            else: number_format = '{}'
            dist_chainage = number_format.format(round(dist_chainage, precision))
        # Afficher la distance
        self.txt_distance.setText(dist_chainage)
        
    """ Méthode appelée quand l'outil est désactivé """
    def deactivate(self):
        if self.isActive():
            # Émettre le signal de desactivation de l'outil
            self.deactivated.emit()
            # Retirer de la carte les géometries créées
            self.canvas.scene().removeItem(self.segment_temporaire)
            self.canvas.scene().removeItem(self.rtss_marker)
            self.canvas.unsetMapTool(self)
            # Désactiver l'outil
            QgsMapTool.deactivate(self)

pass
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        