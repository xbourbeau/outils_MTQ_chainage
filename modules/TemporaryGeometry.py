# -*- coding: utf-8 -*-
from qgis.gui import QgsVertexMarker, QgsMapCanvas, QgsRubberBand
from qgis.core import QgsSymbol
from qgis.PyQt.QtGui import QColor, QTransform
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtCore import Qt, QPointF

from .PluginParametres import PluginParametres

class CustomMarkerDirection(QgsVertexMarker):
    def __init__(self, canvas):
        super().__init__(canvas)
        size = 3
        offset = 11
        # Draw a custom triangle with a offset
        self.polygon = [
            QPointF(0, - size - offset),
            QPointF(-size, size - offset),
            QPointF(size, size - offset)]

    def paint(self, painter):
        # Customize marker appearance
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(self.polygon)

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
        marker.setFillColor(QColor("#178e0c"))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        marker.setPenWidth(1)
        return marker
    
    @staticmethod
    def createMarkerDistanceSnap(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la localisation
        de la souris sur le RTSS dans la carte.
        Le symbole créer est un carrée

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker pour le maptool 
        """
        marker = QgsVertexMarker(canvas)
        marker.setColor(QColor(PluginParametres().getValue("mesure_line_color")))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_BOX)
        marker.setPenWidth(3)
        
        return marker
    
    @staticmethod
    def createMarkerDistanceExt(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la localisation
        de la souris sur le RTSS dans la carte.
        Le symbole créer est un cercle

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker pour le maptool 
        """
        marker = QgsVertexMarker(canvas)
        color = QColor(PluginParametres().getValue("mesure_line_color"))
        marker.setColor(color)
        marker.setFillColor(color)
        marker.setIconSize(8)
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        marker.setPenWidth(1)
        
        return marker
    
    @staticmethod
    def createGeometryDistance(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsRubberBand pour montrer la localisation
        de la ligne de mesure le long du RTSS sur la carte.
        Le symbole créer est une ligne transparante

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsRubberBand: La geometrie temporaire pour le maptool 
        """
        segment = QgsRubberBand(canvas)
        color = QColor(PluginParametres().getValue("mesure_line_color"))
        segment.setColor(color)
        segment.setWidth(3)
        return segment
    
    @staticmethod
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
    
    @staticmethod
    def createMarkerDirection(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la direction
        du RTSS la plus proche de la souris dans la carte.
        Le symbole créer est un triangle noir

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker pour la direction du RTSS
        """      
        # Define le pointeur du chainage
        marker = CustomMarkerDirection(canvas)
        marker.setIconSize(25)
        return marker
    
    @staticmethod
    def createSnappingLine(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsRubberBand pour montrer la ligne
        de snap sur la carte.
        Le symbole créer est une ligne pointillé rose

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsRubberBand: La geometrie temporaire 
        """
        segment = QgsRubberBand(canvas)
        color = QColor("#df05c6")
        color.setAlpha(90)
        segment.setColor(color)
        segment.setLineStyle(Qt.DashDotDotLine)
        segment.setWidth(2)
        return segment
    
    @staticmethod
    def createMarkerNewPoint(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsVertexMarker pour montrer la localisation
        sur du nouveau point à placer dans la carte.
        Le symbole créer est un cerle rouge

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsVertexMarker: Le marker du nouveau point
        """
        # Define le pointeur du chainage
        marker = QgsVertexMarker(canvas)
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        color = QColor("#ff0105")
        marker.setColor(color)
        color.setAlpha(60)
        marker.setFillColor(color)
        marker.setIconSize(7)
        marker.setPenWidth(1)
        return marker
    
    @staticmethod
    def createNewGeom(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsRubberBand pour montrer la ligne
        de snap sur la carte.
        Le symbole créer est une ligne rouge

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsRubberBand: La geometrie temporaire 
        """
        segment = QgsRubberBand(canvas)
        color = QColor("#ff0105")
        segment.setColor(color)
        color.setAlpha(60)
        segment.setFillColor(color)
        segment.setWidth(1)
        return segment
    
    @staticmethod
    def createNewGeomProlongation(canvas:QgsMapCanvas):
        """
        Méthode qui permet de créer un QgsRubberBand pour montrer la ligne
        de snap sur la carte.
        Le symbole créer est une ligne rouge

        Args:
            canvas (QgsMapCanvas): La référence de la carte

        Returns:
            QgsRubberBand: La geometrie temporaire 
        """
        segment = QgsRubberBand(canvas)
        color = QColor("#ff0105")
        segment.setColor(color)
        color.setAlpha(60)
        segment.setFillColor(color)
        segment.setLineStyle(Qt.DotLine)
        segment.setWidth(1)
        return segment