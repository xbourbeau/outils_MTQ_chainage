# -*- coding: utf-8 -*-

from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsVectorLayer, QgsFeature)
import os

def copyVectorLayer(source_layer: QgsVectorLayer, epsg=None):
    if not source_layer.isValid():
        raise ValueError("Invalid source layer.")
    
    if source_layer.geometryType() == 0: source = "Point"
    elif source_layer.geometryType() == 1: source = "LineString"
    elif source_layer.geometryType() == 2: source = "Polygon"
    
    # Create an empty destination layer with the same fields and geometry type
    destination_layer = QgsVectorLayer(source, source_layer.name() + "_copy", "memory")
    # Indicateur qu'il faut reprojecter la couche ou non
    needs_reprojection = epsg is not None and epsg != int(source_layer.crs().authid().split(":")[1])
    # Définir le CRS de la couche en sorti 
    if needs_reprojection:
        crs = QgsCoordinateReferenceSystem(epsg)
        transform = QgsCoordinateTransform(source_layer.crs(), crs, QgsProject.instance().transformContext())
    else: crs = source_layer.crs()
    destination_layer.setCrs(crs)
    
    # Définir les attributs de la couche
    destination_layer.dataProvider().addAttributes(source_layer.fields())
    destination_layer.updateFields()
    
    if needs_reprojection:
        feats=[]
        # Copy features from the source layer to the destination layer
        for feat in source_layer.getFeatures():
            new_feat = QgsFeature()
            geom = feat.geometry()
            geom.transform(transform)
            new_feat.setGeometry(geom)
            new_feat.setAttributes(feat.attributes())
            feats.append(new_feat)
    else: feats = [feat for feat in source_layer.getFeatures()]
    
    destination_layer.dataProvider().addFeatures(feats)

    return destination_layer

def validateLayer(layer_name:str, fields_name=[], geom_type=None):
    """
    Fonction qui valide si une couche avec des champs et géometrie existe dans le projet.
    Args:
        layer_name (str): Nom de la couche
        fields_name (list of str): Nom des champs que la couche doit contenir
        geom_type (int): Le type de géometrie de la couche
    """
    # Vérifier pour chaque couche avec le même nom laquel est la bonne
    for layer in QgsProject.instance().mapLayersByName(layer_name):
        if layer.type() == 0:
            if geom_type is None or layer.geometryType() == geom_type:
                # Vérifier si le champs se retrouve dans la couche
                liste_fields = [field.name() for field in layer.fields()]
                if set(fields_name).issubset(liste_fields): return layer    
    # Not Succesful
    return None 

def isLayerInGeopackage(geopackage, layer_name):
    """
    Fonction qui permet de vérifier si un couche est dans un géopackage

    Args:
        - geopackage (str): Chemin vers le géopackage à vérifier
        - layer_name (str): Le nom de la couche à vérifier dans le géopackage
    """
    if not os.path.exists(geopackage): return False
    source = f"""{geopackage}|subset=SELECT * FROM gpkg_contents WHERE "table_name" LIKE '{layer_name}'"""
    for i in QgsVectorLayer(source, "names", "ogr").getFeatures(): return True
    return False