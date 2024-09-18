# -*- coding: utf-8 -*-
from qgis.core import QgsField, QgsVectorLayer
from qgis.PyQt.QtCore import QVariant
from .PluginParametres import PluginParametres

from ..functions.addLayerToMap import addLayerToMap
from ..mtq.functions import validateLayer

class PluginTemporaryLayer:
    
    def __init__(self) -> None:
        pass

    @staticmethod
    def getLayerEcusson(canvas, crs_authid):
        """
        Permet de créer ou retourner la couche temporaire pour les écussons

        Args:
            canvas (QgsMapCanvas): La référence de la carte
            crs_authid (str): L'authid de la projection de la couche ex: "EPSG:3798"

        Returns (QgsVectorLayer): Couche temporaire pour les écussons
        """
        params = PluginParametres()
        layer_name = params.getValue("layer_ecusson_name")
        field_route = params.getValue("layer_ecusson_field_route")
        field_class = params.getValue("layer_ecusson_field_classe")
        
        # Rétourner la couche existante si elle est dans le projet
        layer = validateLayer(layer_name, fields_name=[field_route], geom_type=0, crs_authid=crs_authid)
        if layer: return layer

        # Create layer
        layer = QgsVectorLayer(f"point?crs={crs_authid}", params.getValue("layer_ecusson_name"), "memory")
        
        # Add fields
        if field_route == '': field_route = "num_route"
        if field_class == field_route or field_class == '': field_class = "Classification"
        
        layer.dataProvider().addAttributes([
            QgsField(field_route, QVariant.String),
            QgsField(field_class, QVariant.String)])
        layer.updateFields()

        return addLayerToMap(canvas, layer, style=params.getValue("layer_ecusson_style"))
    
    @staticmethod
    def createLayerChainage(canvas, crs_authid):
        """
        Permet de creer une couche temporaire pour ajouter les points de recheche des chainages

        Args:
            canvas (QgsMapCanvas): La référence de la carte
            crs_authid (str): L'authid de la projection de la couche ex: "EPSG:3798"

        Returns (QgsVectorLayer): Couche temporaire résulante
        """
        params = PluginParametres()
        layer_name = params.getValue("layer_recherche_chainage_name")

        # Rétourner la couche existante si elle est dans le projet
        layer = validateLayer(layer_name, geom_type=0, crs_authid=crs_authid)
        if layer: return layer

        # Create layer
        layer = QgsVectorLayer(f"point?crs={crs_authid}", layer_name, "memory")
        return addLayerToMap(canvas, layer)