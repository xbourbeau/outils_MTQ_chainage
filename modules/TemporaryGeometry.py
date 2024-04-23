# -*- coding: utf-8 -*-
from qgis.gui import QgsVertexMarker, QgsMapCanvas, QgsRubberBand
from qgis.PyQt.QtGui import QColor

from .PluginParametres import PluginParametres

class TemporaryGeometry:

    def __init__(self) -> None:
        pass

    @staticmethod
    def createMarkerEcusson(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la localisation
        de l'écusson à ajouter dans la carte.
        Le symbole créer est un X vert

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker pour le maptool
        """
        marker = QgsVertexMarker(canvas)
        marker.setColor(QColor("#178e0c"))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_X)
        marker.setPenWidth(3)
        return marker
    
    @staticmethod
    def createMarkerDistance(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la localisation
        de la souris sur le RTSS dans la carte.
        Le symbole créer est un X orange

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker pour le maptool 
        """
        marker = QgsVertexMarker(canvas)
        marker.setColor(QColor("#e4741e"))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_X)
        marker.setPenWidth(3)
        
        return marker
    
    def createGeometryDistance(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsRubberBand pour montrer la localisation
        de la ligne de mesure le long du RTSS sur la carte.
        Le symbole créer est une ligne orange transparante

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsRubberBand: La geometrie temporaire pour le maptool 
        """
        segment = QgsRubberBand(canvas)
        color = QColor(PluginParametres().getValue("mesure_line_color"))
        color.setAlpha(180)
        segment.setColor(color)
        segment.setWidth(3)
        return segment
    
    def createMarkerChainage(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la localisation
        sur le RTSS la plus proche de la souris dans la carte.
        Le symbole créer est un X noir

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker pour le suivi du chainage
        """
        # Define le pointeur du chainage
        marker = QgsVertexMarker(canvas)
        marker.setIconType(QgsVertexMarker.ICON_X)
        marker.setColor(QColor("#000000"))
        marker.setIconSize(10)
        marker.setPenWidth(2)
        return marker