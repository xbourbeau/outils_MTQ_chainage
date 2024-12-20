# -*- coding: utf-8 -*-
from qgis.core import QgsGeometry, QgsPointXY
from qgis.gui import QgisInterface
import os
import math
from .reprojections import reprojectGeometry
from ..layers.WFSLayerMTQ import WFSLayerMTQ

def openSIGO(zoom_level:int=None, center_point:QgsPointXY=None, layers_wms={}, planiactif=False):
    """
    Permet d'ouvrir une fenêtre de SIGO selon les paramètres de l'URL

    Args:
        zoom_level (int, optional): Le niveau de zoom de la vue SIGO. Defaults to None.
        center_point (QgsPointXY, optional): Le centre de la vue SIGO. Defaults to None.
        layers_wms (dict, optional): Dictionnaire qui contient les URL et les noms des couche à ajouter. Defaults to {}.
        planiactif (bool): Replacer le lien SIGO par PlaniActif
    """
    if planiactif: default_link = "https://planiactifs.transports.qc/?context=_default"
    # Lien par défaut pour ouvrir SIGO
    else: default_link = "https://www.geomsp.qc/igo2/transports-quebec/?context=_default"
    # Ajouter un niveau de zoom
    if zoom_level: default_link += f"&zoom={zoom_level}"
    # Ajouter un point de centre
    if center_point: default_link += f"&center={center_point.x()},{center_point.y()}"

    # Ajouter des couches WFS à montrer
    if layers_wms:
        urls, wms_layers = "wmsUrl=", "wmsLayers="
        for url, layers in layers_wms.items():
            urls += url + ","
            wms_layers += "(" + ','.join(layers) + "),"
        default_link += f"&{urls[:-1]}&{wms_layers[:-1]}"
    # Ouvrir SIGO avec le lien
    os.startfile(default_link)

def openMapInSIGO(iface:QgisInterface, layers=None, planiactif=False):
    """
    Fonction qui permet d'ouvrir SIGO selon l'étendue de la carte.
    Des couches peuvent êtres spécifier au besoin

    Args:
        - iface: iface de QGIS
        - layers (LayerManager): Le gestionnaire des couches
    """
    canvas = iface.mapCanvas()
    # Définir le niveau de zoom de la vue
    scale = canvas.scale()
    dpi = iface.mainWindow().physicalDpiX()
    zoom_level = int(round(math.log(((dpi* 39.37 * 156543.04) / scale), 2), 0))
    # Définir le centre de la vue
    center_point = reprojectGeometry(QgsGeometry.fromPointXY(canvas.center()), canvas.mapSettings().destinationCrs(), 4326).asPoint()
    if center_point.x() == 0.0 and center_point.y() == 0.0: center_point = None

    layers_wms = {}
    if layers:
        for layer_name in layers:
            layer:WFSLayerMTQ = layers.get(layer_name)
            if layer.dataProvider().lower() != "wfs": continue
            if not layers.isLayerInProject(layer_name, use_name=False, use_source=True): continue
            type_name = layer.typename()
            if "ms:" in type_name: type_name = type_name.replace("ms:", "")
            if layer.url() in layers_wms: layers_wms[layer.url()].append(type_name)
            else: layers_wms[layer.url()] = [type_name]

    # Ouvrir SIGO avec les paramètres suivant
    openSIGO(zoom_level=zoom_level, center_point=center_point, layers_wms=layers_wms, planiactif=planiactif)

def openLayersInSIGO(layers:list[WFSLayerMTQ], iface:QgisInterface=None, planiactif=False):
    """
    Fonction qui permet d'ouvrir SIGO avec des couches spécifiée

    Args:
        - layers (list[WFSLayerMTQ]): Liste des couches à ajouter dans SIGO
        - iface (QgisInterface): L'interface pour avoir une localisation de carte
    """
    layers_wms = {}
    for layer in layers:
        if layer.dataProvider().lower() != "wfs": continue
        type_name = layer.typename()
        if "ms:" in type_name: type_name = type_name.replace("ms:", "")
        if layer.url() in layers_wms: layers_wms[layer.url()].append(type_name)
        else: layers_wms[layer.url()] = [type_name]

    zoom_level, center_point = None, None
    if iface:
        canvas = iface.mapCanvas()
        if canvas:
            # Définir le niveau de zoom de la vue
            scale = canvas.scale()
            dpi = iface.mainWindow().physicalDpiX()
            zoom_level = int(round(math.log(((dpi* 39.37 * 156543.04) / scale), 2), 0))
            # Définir le centre de la vue
            center_point = reprojectGeometry(QgsGeometry.fromPointXY(canvas.center()), canvas.mapSettings().destinationCrs(), 4326).asPoint()
            if center_point.x() == 0.0 and center_point.y() == 0.0: center_point = None

    # Ouvrir la vue sigo sur les couches
    openSIGO(layers_wms=layers_wms, zoom_level=zoom_level, center_point=center_point, planiactif=planiactif)