# -*- coding: utf-8 -*-
from qgis.core import QgsGeometry
from qgis.gui import QgisInterface
import os
import math
from .reprojections import reprojectGeometry

def openSIGO(iface:QgisInterface, layers=None):
    """
    Fonction qui permet d'ouvrir SIGO selon l'étendue de la carte.

    Args:
        - iface: iface de QGIS
        - layers (LayerManager): Le gestionnaire de couche pour ajouter les couches de la carte dans SIGO
    """
    default_link = "https://www.geomsp.qc/igo2/transports-quebec/"
    canvas = iface.mapCanvas()
    scale = canvas.scale()
    dpi = iface.mainWindow().physicalDpiX()
    zoom_level = int(round(math.log(((dpi* 39.37 * 156543.04) / scale), 2), 0))
    center_point = reprojectGeometry(QgsGeometry.fromPointXY(canvas.center()), canvas.mapSettings().destinationCrs(), 4326).asPoint()
    if center_point.x() != 0.0 or center_point.y() != 0.0:
        layers_wms = {}
        if layers:
            for layer_name in layers.getLayersName():
                if layers.getDataProvider(layer_name) == "wfs":
                    if layers.isLayerInProject(layer_name, use_name=False, use_source=True):
                        url = layers.getLayerSource(layer_name)["url"]
                        type_name = layers.getLayerSource(layer_name)["typename"]
                        if "ms:" in type_name: type_name = type_name.replace("ms:", "")
                        if url in layers_wms: layers_wms[url].append(type_name)
                        else: layers_wms[url] = [type_name]
        if layers_wms:
            urls, wms_layers = "wmsUrl=", "wmsLayers="
            for url, layers in layers_wms.items():
                urls += url + ","
                wms_layers += "(" + ','.join(layers) + "),"
            default_link = f"https://www.geomsp.qc/igo2/transports-quebec/?context=_default&zoom={zoom_level}&center={center_point.x()},{center_point.y()}&{urls[:-1]}&{wms_layers[:-1]}"
        else: default_link = f"https://www.geomsp.qc/igo2/transports-quebec/?context=_default&zoom={zoom_level}&center={center_point.x()},{center_point.y()}"
    os.startfile(default_link)