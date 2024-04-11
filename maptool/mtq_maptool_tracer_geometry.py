# -*- coding: utf-8 -*-

from ..interfaces.fenetre_add_feature import fenetreAddFeature
from ..gestion_parametres import sourceParametre
from qgis.core import QgsProject, QgsGeometry, QgsApplication, Qgis
from qgis.gui import QgsMapTool, QgsMapToolEdit, QgsRubberBand, QgsVertexMarker
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from qgis.PyQt.QtWidgets import QMenu, QMessageBox, QToolButton
from qgis.PyQt.QtGui import QColor

class MtqMapToolTracerGeometry(QgsMapToolEdit):

    points = pyqtSignal(list)
    
    def __init__(self, iface, geocode):
        self.iface = iface
        # Reference de la carte
        self.canvas = self.iface.mapCanvas()
        # Objet de géocodage
        self.geocode = geocode
        # Référence de la couche des RTSS
        self.layer_rtss = None
        # Référence à l'interface de l'outil
        self.dlg = fenetreAddFeature(self.iface, self.geocode)
        
        # Créer un instance de l'outil d'edition sur la carte
        QgsMapToolEdit.__init__(self, self.canvas)
        
        # Connecter le bouton Annuler au reset
        self.dlg.btn_annuler.clicked.connect(self.reset)
        # Garder en mémoire la position de la fenêtre
        self.dlg.dockLocationChanged.connect(lambda area: self.gestion_parametre.getParam("dlg_add_feat_last_pos").setValue(area))
        
        # Référence aux paramètres
        self.gestion_parametre = sourceParametre()
        # Valeur de précision
        self.precision = 0
        # Dernier RTSS qui a clignoté
        self.last_flash = None
        # Définition du curseur
        self.mCursor = QgsApplication.getThemeCursor(4)
    
    def activate(self):
        # Paramétrer le nombre de clique à 0
        self.nb_click = 0
        # Activer le curseur
        self.canvas.setCursor(self.mCursor)
        if self.dlg.isVisible(): self.dlg.raise_()
        else:
            geom_l = self.createRubberBand(Qgis.GeometryType.Line)
            geom_p = self.createRubberBand(Qgis.GeometryType.Point)
            geom_s = self.createRubberBand(Qgis.GeometryType.Polygon)
            print([geom_p, geom_l, geom_s])
            self.dlg.setGeometries([geom_p, geom_l, geom_s])
            # show the dockwidget
            self.iface.addTabifiedDockWidget(self.gestion_parametre.getParam("dlg_add_feat_last_pos").getValue(), self.dlg, raiseTab=True)
            # Afficher la fenêtre
            self.dlg.show()
            
    
    def setLayer(self, layer_id): self.layer_rtss = self.layer(layer_id)
    
    """ Réinitialiser l'outil """
    def reset(self):
        # Réinitialiser le nombre de clique à 0
        self.nb_click = 0
        # Reset le RTSS
        self.feat_rtss = None
        # Réinitialise les valeurs des points
        self.chainage_1, self.chainage_2, self.chainage_3, self.chainage_4 = 0, 0, 0, 0
        self.dist_1, self.dist_2, self.dist_3, self.dist_4 = 0, 0, 0, 0
        # Désactiver le traçage parallèle ou perpendiculaire au RTSS
        self.dlg.gbx_trace_poly.setEnabled(False)
    
    def updateEditingLayer(self, layer):
        print(layer)
        self.dlg.updateCurrentLayer(layer)
    
    """
    Méthode activé quand la carte est cliquée
    Paramètre entrée:
        - e (QgsMouseEvent) = Objet regroupant les information sur le click de la carte
    """
    def canvasPressEvent( self, e):
        # Click Gauche   
        if e.button() == 1:
            self.nb_click += 1
            # Calculer la position du curseur
            geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        #--------------- Tracage 1er point et paramétrage du RTSS -------------------------------
            if self.nb_click == 1:
                # Permettre le traçage parallèle ou perpendiculaire au RTSS
                self.dlg.gbx_trace_poly.setEnabled(True)
                # Désactiver l'option de rendre les segments parallèles ou perpendiculaires au RTSS
                for self.dlg.perp in self.dlg.perp_list: self.dlg.perp.setEnabled(False)
                for self.dlg.para in self.dlg.para_list: self.dlg.para.setEnabled(False)
                # Trouver les RTSS les plus proches
                list_rtss = self.geocode.nearestRTSS(geom, 5, 30)
                # Choisir le RTSS quand il est unique
                if len(list_rtss) == 1: feat_rtss = list_rtss[0]['rtss']
                # Afficher la liste des RTSS quand il y a plusieurs RTSS à proximité
                elif len(list_rtss) > 1: feat_rtss = self.geocode.getRTSS(self.showMenuChoix(list_rtss, e.globalPos()))
                if len(list_rtss) >= 1:
                    # Paramétrage du RTSS
                    if feat_rtss:
                        self.feat_rtss = feat_rtss
                        self.dlg.txt_rtss.setText(self.feat_rtss.getRTSS())
                        # Position du 1er point
                        self.chainage_1 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
                        self.dist_1 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
                        self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_1, self.dist_1, self.chainage_1 ,self.dist_1 ,self.chainage_1 ,self.dist_1])
                        # Réinitialiser si un point est en cours de traçage
                        if self.dlg.geomType == 1: self.reset()
                    # Réinitialiser le choix de RTSS si aucun n'a été choisi
                    else:
                        self.nb_click = 0
                else: 
                    widget = self.iface.messageBar().createMessage("Cliquez plus proche d'un RTSS pour commencer le traçage.")
                    self.iface.messageBar().pushWidget(widget, Qgis.Critical, duration=3)
                    self.nb_click = 0
            #-------------- Tracage 2e point --------------------
            elif self.nb_click == 2:
                self.chainage_2 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
                self.dist_2 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
                # Lorsque parallèle
                if self.dlg.chx_parallele_L.isChecked() or self.dlg.chk_parallel_Pol.isChecked():
                    self.dist_2 = self.dist_1
                    self.dlg.chk_parallel_Pol.setCheckState(Qt.Unchecked)
                # Lorsque perpendiculaire
                elif self.dlg.chx_perpendiculaire_L.isChecked() or self.dlg.chx_perpendiculaire_Pol.isChecked():
                    self.chainage_2 = self.chainage_1
                    self.dlg.chx_perpendiculaire_Pol.setCheckState(Qt.Unchecked)
                if self.dlg.geomType == 0:
                    # Vérifier la validité de la géométrie
                    self.geom_l = self.dlg.geom_line.asGeometry()
                    if self.geom_l.isGeosValid():
                        self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_1 ,self.dist_1 ,self.chainage_1 ,self.dist_1])
                        # Réinitialiser si une ligne est en cours de traçage
                        self.reset()
                    else:
                        widget = self.iface.messageBar().createMessage("La géométrie de la ligne est invalide, veuillez repositionner les points.")
                        self.iface.messageBar().pushWidget(widget, Qgis.Critical, duration=3)
                        self.nb_click = 1
            #-------------- Tracage 3e point --------------------
            elif self.nb_click == 3:
                self.chainage_3 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
                self.dist_3 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
                # Lorsque parallèle
                if self.dlg.chk_parallel_Pol.isChecked():
                    self.dist_3 = self.dist_2
                    self.dlg.chk_parallel_Pol.setCheckState(Qt.Unchecked)
                # Lorsque perpendiculaire
                elif self.dlg.chx_perpendiculaire_Pol.isChecked():
                    self.chainage_3 = self.chainage_2
                    self.dlg.chx_perpendiculaire_Pol.setCheckState(Qt.Unchecked)
                self.geom_p = self.dlg.geom_poly.asGeometry()
                # Vérifier la validité de la géométrie
                if self.geom_p.isGeosValid():
                    self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_3 ,self.chainage_1 ,self.dist_1])
                else:
                    widget = self.iface.messageBar().createMessage("La géométrie du polygone est invalide, veuillez repositionner le point.")
                    self.iface.messageBar().pushWidget(widget, Qgis.Critical, duration=3)
                    self.nb_click = 2
            #-------------- Tracage 4e point --------------------
            elif self.nb_click == 4:
                self.chainage_4 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
                self.dist_4 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
                # Lorsque parallèle
                if self.dlg.chk_parallel_Pol.isChecked():
                    self.dist_4 = self.dist_3
                    self.dlg.chk_parallel_Pol.setCheckState(Qt.Unchecked)
                # Lorsque perpendiculaire
                elif self.dlg.chx_perpendiculaire_Pol.isChecked():
                    self.chainage_4 = self.chainage_3
                    self.dlg.chx_perpendiculaire_Pol.setCheckState(Qt.Unchecked)
                self.geom_p = self.dlg.geom_poly.asGeometry()
                # Vérifier la validité de la géométrie
                if self.geom_p.isGeosValid():
                    self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_3 ,self.chainage_4 ,self.dist_4])
                    self.reset()
                else:
                    widget = self.iface.messageBar().createMessage("La géométrie du polygone est invalide, veuillez repositionner le point.")
                    self.iface.messageBar().pushWidget(widget, Qgis.Critical, duration=3)
                    self.nb_click = 3
                # Activer l'option de rendre les segments parallèles ou perpendiculaires au RTSS
                for self.dlg.perp in self.dlg.perp_list: self.dlg.perp.setEnabled(True)
                for self.dlg.para in self.dlg.para_list: self.dlg.para.setEnabled(True)
        # Click Droit
        else: 
            self.reset()
    
    """
        Méthode activé quand le curseur se déplace dans la carte
        Entrée:
            - e (QgsMouseEvent) = Objet regroupant les information sur la position du curseur
                                    dans la carte
    """
    def canvasMoveEvent(self, e):
        # Geometrie du point du cursor dans la projection de la couche des RTSS
        geom = QgsGeometry.fromPointXY(self.toLayerCoordinates(self.layer_rtss, e.pos()))
        # Tracking de la position du point 2 lors du traçage
        if self.nb_click == 1:
            self.chainage_2 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
            self.dist_2 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
            # Lorsque parallèle
            if self.dlg.chx_parallele_L.isChecked() or self.dlg.chk_parallel_Pol.isChecked():
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_1, self.chainage_1 ,self.dist_1 ,self.chainage_1 ,self.dist_1])
            # Lorsque perpendiculaire
            elif self.dlg.chx_perpendiculaire_L.isChecked() or self.dlg.chx_perpendiculaire_Pol.isChecked():
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_1, self.dist_2, self.chainage_1 ,self.dist_1 ,self.chainage_1 ,self.dist_1])
            # Rien de coché
            else:
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_2 ,self.dist_2 ,self.chainage_1 ,self.dist_1])
        # Tracking de la position du point 3 lors du traçage
        elif self.nb_click == 2:
            self.chainage_3 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
            self.dist_3 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
            # Lorsque parallèle
            if self.dlg.chk_parallel_Pol.isChecked():
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_2 ,self.chainage_1 ,self.dist_1])
            # Lorsque perpendiculaire
            elif self.dlg.chx_perpendiculaire_Pol.isChecked():
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_2 ,self.dist_3 ,self.chainage_1 ,self.dist_1])
            # Rien de coché
            else:
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_3 ,self.chainage_1 ,self.dist_1])
        # Tracking de la position du point 4 lors du traçage
        elif self.nb_click == 3:
            self.chainage_4 = round(self.feat_rtss.getChainageFromPoint(geom), self.precision)
            self.dist_4 = round(self.feat_rtss.getDistanceFromPoint(geom.asPoint()), 1)
            # Lorsque parallèle
            if self.dlg.chk_parallel_Pol.isChecked():
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_3 ,self.chainage_4 ,self.dist_3])
            # Lorsque perpendiculaire
            elif self.dlg.chx_perpendiculaire_Pol.isChecked():
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_3 ,self.chainage_3 ,self.dist_4])
            # Rien de coché
            else:
                self.dlg.listInformation([self.feat_rtss, self.chainage_1, self.dist_1, self.chainage_2, self.dist_2, self.chainage_3 ,self.dist_3 ,self.chainage_4 ,self.dist_4]) 

                   
    """ Méthode qui permet de faire clignoter la géometrie de l'option survolée dans le menu """
    def flashMenuItem(self, action):
        # Vérifier si l'entité ne vient pas d'être flashé 
        if action.text() != self.last_flash:
            # Garder en mémoire l'entité qui vient d'être flashé 
            self.last_flash = action.text()
            # Flasher la géometrie du RTSS survolé dans le menu
            self.canvas.flashGeometries([self.geocode.getRTSS(action.text()).getGeometry()], self.layer_rtss.crs(), flashes=1, duration=200)
    
    """ Méthode qui permet de montrer le menu contenant les choixs de RTSS et de retourner le RTSS selectionné """
    def showMenuChoix(self, list_rtss, pos):
        menu = QMenu()
        # Faire clignoter la géometrie du RTSS dont la souris est par dessus dans le menu
        menu.hovered.connect(self.flashMenuItem)
        # Ajouter les options au menu
        for rtss in list_rtss: action = menu.addAction(rtss['rtss'].getRTSS(formater=True))
        # Montrer le menu 
        choix = menu.exec_(pos)
        # Lorsque le choix est fait, déconnecter la méthode du menu
        menu.hovered.disconnect(self.flashMenuItem)
        return "" if choix is None else choix.text()
        
    
    def deactivate(self):
        self.dlg.close()
        # Émettre le signal de desactivation de l'outil
        self.deactivated.emit()
        self.canvas.unsetMapTool(self)
        # Désactiver l'outil
        QgsMapTool.deactivate(self)    
pass