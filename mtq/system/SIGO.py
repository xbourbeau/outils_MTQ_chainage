# -*- coding: utf-8 -*-
from qgis.core import QgsGeometry, QgsPointXY, QgsRectangle
from qgis.gui import QgisInterface
from typing import Dict, List, Optional
import os
import math
from ..functions.reprojections import reprojectGeometry, reprojectExtent, reprojectPoint
from ..layers.WFSLayerMTQ import WFSLayerMTQ

# DEV: Ajouter une manière de faire une recherche à partir du lien:
""" &exactMatch=1&searchGeom=1&search=154980784#pps """
""" &exactMatch=1&searchGeom=1&search=-70.76049045300132,45.67372128212189 """

class SIGO:

    def __init__(self, default_url="https://igo.mtq.min.intra/tq/sigo/?context=_default"):
        self.default_url = default_url
        self.default_crs = 4326

    def getURL(self, zoom_level:int=None, center_point:QgsPointXY=None, layers_wms={}, search=None):
        """
        Permet dde créer les paramètres de l'URL pour ouvrir SIGO

        Args:
            zoom_level (int, optional): Le niveau de zoom de la vue SIGO. Defaults to None.
            center_point (QgsPointXY, optional): Le centre de la vue SIGO. Defaults to None.
            layers_wms (dict, optional): Dictionnaire qui contient les URL et les noms des couche à ajouter. Defaults to {}.
        """
        # Lien SIGO par défault
        default_url = self.getDefaultURL()
        # Ajouter un niveau de zoom
        if zoom_level: default_url += f"&zoom={zoom_level}"
        # Ajouter un point de centre
        if center_point: default_url += f"&center={center_point.x()},{center_point.y()}"
        # Ajouter des couches
        if layers_wms: default_url += self._build_wms_parameters(layers_wms)
        # Ajouter une recherche
        if search: default_url += f"&searchGeom=0&search={search}"
        # Retourner le lien vers SIGO
        return default_url
    
    def getURLFromPoint(self, center_point:QgsPointXY, zoom_level:int=None, layers_wms={}, search=None, crs=4326):
        reprojected_point = reprojectPoint(center_point, crs, 4326)
        return self.getURL(zoom_level=zoom_level, center_point=reprojected_point, layers_wms=layers_wms, search=search)

    def getURLFromMap(self, iface:QgisInterface, layers=None, search=None):
        """
        Permet d'ouvrir SIGO selon l'étendue de la carte.
        Des couches peuvent êtres spécifier au besoin

        Args:
            - iface: iface de QGIS
            - layers (LayerManager): Le gestionnaire des couches
        """
        # Définir le canvas
        canvas = iface.mapCanvas()
        # Définir le niveau de zoom de la vue
        zoom_level = self._calculate_zoom_level(
            scale=canvas.scale(),
            dpi=iface.mainWindow().physicalDpiX())
        # Définir le centre de la vue
        center_point = self._get_canvas_center(canvas)

        layers_wms = {}
        if layers:
            list_layers = []
            for layer_name in layers:
                layer:WFSLayerMTQ = layers.get(layer_name)
                if layer.dataProvider().lower() != "wfs": continue
                if not layers.isLayerInProject(layer_name, use_name=False, use_source=True): continue
                list_layers.append(layer)

            layers_wms = self._build_wms_layers(list_layers)

        return self.getURL(zoom_level=zoom_level, center_point=center_point, layers_wms=layers_wms, search=search)

    def getURLFromLayers(self, layers:list[WFSLayerMTQ], iface:QgisInterface=None, search=None):
        """
        Permet d'ouvrir SIGO avec des couches spécifiée

        Args:
            - layers (list[WFSLayerMTQ]): Liste des couches à ajouter dans SIGO
            - iface (QgisInterface): L'interface pour avoir une localisation de carte
        """
        layers_wms = self._build_wms_layers(layers)

        zoom_level, center_point = None, None
        if iface:
            canvas = iface.mapCanvas()
            if canvas:
                # Définir le niveau de zoom de la vue
                scale = canvas.scale()
                dpi = iface.mainWindow().physicalDpiX()
                zoom_level = self._calculate_zoom_level(scale, dpi)
                # Définir le centre de la vue
                center_point = reprojectGeometry(QgsGeometry.fromPointXY(canvas.center()), canvas.mapSettings().destinationCrs(), 4326).asPoint()
                if center_point.x() == 0.0 and center_point.y() == 0.0: center_point = None

        return self.getURL(zoom_level, center_point, layers_wms, search=search)

    def getURLFromExtent(self, extent:QgsRectangle, max_zoom=19, offset=2, layers_wms={}, crs=4326, search=None):
        """
        Calculate center point and zoom level for a web map URL based on a QgsRectangle extent.
        
        Args:
            extent (QgsRectangle): The extent to calculate parameters for in Epsg:4326
            tile_size (int): The tile size in pixels (default 256)
            max_zoom (int): Maximum zoom level to consider (default 19)
            offset (int): Ajouter des niveau de zoom a celui calculer
            crs (int): Le CRS de l'étendu
        
        Returns:
            tuple: (center_lon, center_lat, zoom_level)
        """
        extent = reprojectExtent(extent, crs, 4326)
        # Get the center point
        center = extent.center()
        # Adjust for latitude to account for mercator projection
        lat_rad_adjust = math.log(1 / math.cos(math.radians(center.y()))) / math.log(2)
        # Calculate the span in degrees
        span_x = abs(extent.xMaximum() - extent.xMinimum())
        zoom = math.log2(360 / span_x) + lat_rad_adjust
        
        # Round to nearest integer and ensure it's within bounds
        zoom = min(round(zoom) + offset, max_zoom)
        zoom = max(zoom, 0)

        return self.getURL(zoom, center, layers_wms, search=search)

    def getDefaultURL(self): return self.default_url
        
    def open(self, zoom_level:int=None, center_point:QgsPointXY=None, layers_wms={}):
        url = self.getURL(zoom_level=zoom_level, center_point=center_point, layers_wms=layers_wms)
        # Ouvrir SIGO avec le lien
        os.startfile(url)  
    
    def openFromMap(self, iface:QgisInterface, layers=None):
        url = self.getURLFromMap(iface, layers)
        # Ouvrir SIGO avec le lien
        os.startfile(url)

    def openFromLayers(self, layers:list[WFSLayerMTQ], iface:QgisInterface=None): 
        url = self.getURLFromLayers(layers, iface)
        # Ouvrir SIGO avec le lien
        os.startfile(url)

    def openFromExtent(self, extent:QgsRectangle, max_zoom=19, offset=2, layers_wms={}, crs=4326):
        url = self.getURLFromExtent(extent, max_zoom, offset, layers_wms, crs)
        # Ouvrir SIGO avec le lien
        os.startfile(url)

    def _calculate_zoom_level(self, scale: float, dpi: float) -> int:
        """ Helper method to calculate zoom level """
        return int(round(math.log(((dpi * 39.37 * 156543.04) / scale), 2), 0))

    def _build_wms_parameters(self, layers_wms: Dict[str, List[str]]) -> str:
        """ Build WMS URL parameters from layers dict """
        if not layers_wms: return ""
        urls = "wmsUrl=" + ",".join(layers_wms.keys())
        layers = "wmsLayers=" + ",".join(f"({','.join(layers)})" for layers in layers_wms.values())
        return f"&{urls}&{layers}"
    
    def _build_wms_layers(self, layers:list[WFSLayerMTQ]):
        layers_wms = {}
        for layer in layers:
            if layer.dataProvider().lower() != "wfs": continue
            type_name = layer.typename()
            if "ms:" in type_name: type_name = type_name.replace("ms:", "")
            layer_url = layer.url().replace("?", "")
            if layer_url in layers_wms: layers_wms[layer_url].append(type_name)
            else: layers_wms[layer_url] = [type_name]
        return layers_wms

    def _get_canvas_center(self, canvas) -> Optional[QgsPointXY]:
        """Get reprojected canvas center point"""
        center = reprojectGeometry(
            QgsGeometry.fromPointXY(canvas.center()),
            canvas.mapSettings().destinationCrs(), 
            self.default_crs).asPoint()
        
        if center.x() == 0.0 and center.y() == 0.0: return None
        return center

