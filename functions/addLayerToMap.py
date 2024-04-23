# -*- coding: utf-8 -*-
from qgis.core import QgsProject, QgsVectorLayer
from qgis.gui import QgsMapCanvas

def addLayerToMap(canvas:QgsMapCanvas, layer:QgsVectorLayer, style=None):
    """ 
    Fonction qui ajoute une couche à une carte. Un style peut également être défini.
    
    Args:
        - canvas(QgsMapCanvas): La carte à update après l'ajout de couche 
        - layer(QgsVectorLayer): La couche à ajouter
        - style(str): Le chemin vers un .qml du style à appliquer
    """
    layer_added = QgsProject.instance().addMapLayer(layer)
    if style and layer_added: layer_added.loadNamedStyle(style)
    # Actualiser le canvas de la carte
    canvas.refresh()
    return layer_added