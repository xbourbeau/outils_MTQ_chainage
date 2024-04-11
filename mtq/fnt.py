# -*- coding: utf-8 -*-

from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeatureRequest, QgsVectorLayer, QgsFeature, QgsGeometry)
import numpy as np
from qgis.PyQt.QtWidgets import QFileDialog
import os.path
import random
from copy import deepcopy
import shapely.ops


'''
Fonction qui inverse la géometrique d'un ligne
Entrée:
    - geom (list coordonnée) = La géometrie a inverser
Sortie:
    - La geometrie inversés
'''
def reverse_geom(geom):
    def _reverse(x, y, z=None):
        if z:
            return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]

    return shapely.ops.transform(_reverse, geom)
    

'''
Fonction compare deux liste de chainage de la même longueur pour savoir si les chainage
s'intersect.
Entrée:
    c_compare (liste) = Liste des chainages #1
    c_source (liste) = Liste des chainages #2

Sortie:
    - (bool) = Si il y a une intersection
'''
def chainageIntersects(c_compare, c_source):
    compare = np.append(np.array(c_compare), np.flip(np.array(c_compare)))
    source = np.append(np.array(c_source), np.array(c_source))
    if compare.size == source.size:
        lesser = np.less_equal(source, compare)
        greater = np.greater_equal(source, compare)
        if np.all(lesser) is np.any(lesser) and np.all(greater) is np.any(greater):
            return False
        return True
        
    return None

# Fonction qui ouvre une fenêtre de dialog pour que l'utilisateur choisi un dossier
def choisirDossier(window_name="Choisir le dossier", default_folder=None):
    folder = os.path.expanduser("~") + '\Desktop\\'
    if default_folder:
        if os.path.exists(default_folder):
            folder = default_folder
        
    chemin = QFileDialog.getExistingDirectory(None, window_name, folder)
    
    if os.path.exists(chemin):
        return chemin + '/'
    else:
        return default_folder

# Fonction qui ouvre une fenêtre de dialog pour que l'utilisateur enregistre un fichier
def saveFichier(window_name="Enregistrer le fichier", ext=".geojson", default_file=None):
    folder = os.path.expanduser("~") + '\Desktop\\'
    if default_file:
        default_file = os.path.realpath(default_file)
        if os.path.exists(os.path.dirname(default_file)):
            # Conserver le nom du dossier où est enregistré le fichier 
            folder = default_file
        
        
    file, extention = QFileDialog.getSaveFileName(None, window_name, folder, ext)
    if file:
        return file
    else:
        return default_file

# Fonction qui ouvre une fenêtre de dialog pour que l'utilisateur choisi un fichier
def choisirFichier(window_name="Choisir le fichier", ext=".txt", default_file=None):
    folder = os.path.expanduser("~") + '\Desktop\\'
    if default_file:
        if os.path.exists(default_file):
            # Conserver le nom du dossier où est enregistré le fichier 
            folder = default_file
        
    file, extention = QFileDialog.getOpenFileName(None, window_name, folder, ext)
    if os.path.exists(file):
        return file
    else:
        return default_file
    
def getWFSRequest(canvas, epsg=3798):
    map_crs = QgsProject.instance().crs().authid()
    crsDest = QgsCoordinateReferenceSystem(epsg)
    crsSrc = QgsCoordinateReferenceSystem(map_crs)
    
    if crsSrc != crsDest:
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        extent = crs_transform.transform(canvas.extent())
    else:
        extent = canvas.extent()

    spatial_request = "ST_Intersects( ST_GeometryFromText('%s'), geometry)" % (extent.asWktPolygon())

    return spatial_request 
            

'''
    Fonction qui permet de choisir une couleur pour chaque entitées d'une couche en fonction de 
    sa proximité avec les autres entitées de la couche. Le nombre de couleur devrait être supérieur
    aux nombres d'entitées pouvant être superposé (distance 0).
    
    Entrée:
        - layer (QgsVectorLayer) = La couche à choisir les couleurs
        - pallette (list) = Une list de valeurs unique représentant les couleurs
        - champ_couleur (str) = Le champ contennat les valeurs de couleur
        - requete (str) = Une requête à appliquer pour filtrer les entitées
'''
def colorPicker(layer, pallette, champ_couleur="color", requete=None):
    # Nombre max de feature à vérifier la proximité
    feat_number = len(pallette)-1
    # La position du champ dans la couche
    field_id = [field.name() for field in layer.fields()].index(champ_couleur)
    request = QgsFeatureRequest()
    if requete: request.setFilterExpression(requete)
    # Mettre la couche en édition si elle ne l'est pas
    if not layer.isEditable(): layer.startEditing()
    # Parcourir les entités de la couche 
    for feat1 in layer.getFeatures(request):
        # Liste des features proche
        list_feat = []
        # Liste des distances des features
        distances = []
        # Reparcourir chaque entités de la couche 
        for feat2 in layer.getFeatures(request):
            # Ignorer l'entité en cours
            if feat2 != feat1:
                # Calculer la distance
                dist = feat1.geometry().distance(feat2.geometry())
                # Vérifier si la list est pleine
                if len(list_feat) == feat_number:
                    # Vérifier si la distance est plus petite que la plus gande de la liste
                    if dist < max(distances):
                        # Trouver la position dans la liste de la distance à retirer 
                        idx_to_remove = distances.index(max(distances))
                        # Retirer les valeurs des listes
                        list_feat.pop(idx_to_remove)
                        distances.pop(idx_to_remove)
                        # Ajouter les nouvelles valeurs
                        list_feat.append(feat2)
                        distances.append(dist)
                else:
                    # Ajouter les valeurs aux listes
                    list_feat.append(feat2)
                    distances.append(dist)
        # Copier la pallette de couleur original
        pallette_choice = deepcopy(pallette)
        # Parcourir les entitées les plus proche
        for feat in list_feat:
            # Indentifier leurs couleurs
            color  = feat[champ_couleur]
            # Retirer la couleur de la pallette des choix possible
            if color in pallette_choice: pallette_choice.remove(color)
        # Choisir une couleur aléatoire dans la pallette resultante
        color_picked = random.choice(pallette_choice)
        # Modifier le champ de couleurs de la couche 
        layer.changeAttributeValue(feat1.id(), field_id, color_picked)

'''
    Fonction qui permet de reprojeter une entitée dans un autres système de coordonnée
    
    Entrée:
        - feat (List of QgsFeatures) = Liste des entitée à reprojeté
        - org_epsg (int) = Code EPSG du CRS des entitées
        - dest_epsg (int) = Code EPSG du CRS des entitées résultantes
        
    Sortie:
        - reproject_feats (List of QgsFeatures) = Liste d'entitée reprojeté
'''
def reprojectFeats(feats, org_epsg, dest_epsg):
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    
    # Vérifier si les CRS sont différent
    if crsSrc != crsDest:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        # Reprojeter les entitées
        reproject_feats = [crs_transform.transform(feat) for feat in feats]
    # Sinon les entitées n'on pas besoin d'être reprojetés
    else: reproject_feats = feats
    
    # Retourner les entitées résultantes
    return reproject_feats


'''
    Fonction qui permet de reprojeter une entitée dans un autres système de coordonnée
    
    Entrée:
        - feat (QgsFeatures) = L'entitée à reprojeté
        - org_epsg (int) = Code EPSG du CRS de l'entitée
        - dest_epsg (int) = Code EPSG du CRS de l'entitée résultante
        
    Sortie:
        - reproject_feat (QgsFeatures) = L'entitée reprojeté
'''
def reprojectFeat(feat, org_epsg, dest_epsg):
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    
    # Vérifier si les CRS sont différent
    if crsSrc != crsDest:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        # Reprojeter l'entitée
        feat.geometry().transform(crs_transform)
    
    # Retourner l'entitée résultante
    return feat

'''
    Fonction qui permet de reprojeter une geometrie dans un autres système de coordonnée
    
    Entrée:
        - geom (QgsGeometry) = La geometrie à reprojeté
        - org_epsg (int) = Code EPSG du CRS de l'entitée
        - dest_epsg (int) = Code EPSG du CRS de l'entitée résultante
        
    Sortie:
        - geom (QgsGeometry) = La geometrie reprojeté
'''
def reprojectGeometry(geom, org_epsg, dest_epsg):
    # Vérifier si les CRS sont différent
    if org_epsg != dest_epsg:
        # Instancier les CRS à partir des codes EPSG
        crsDest = QgsCoordinateReferenceSystem(dest_epsg)
        crsSrc = QgsCoordinateReferenceSystem(org_epsg)
        if crsDest.isValid() and crsSrc.isValid():
            # Instancier la méthode de transformation entre les deux CRS
            crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
            # Reprojeter l'entitée
            geom.transform(crs_transform)
        else: return False
    
    # Retourner l'entitée résultante
    return geom

'''
    Fonction qui permet de reprojeter un étendu dans un autres système de coordonnée
    
    Entrée:
        - feat (QgsRectangle) = L'extent à reprojeté
        - org_epsg (int) = Code EPSG du CRS de l'entitée
        - dest_epsg (int) = Code EPSG du CRS de l'entitée résultante
        
    Sortie:
        - reproject_extent (QgsRectangle) = L'extent reprojeté
'''
def reprojectExtent(extent, org_epsg, dest_epsg):
    # Vérifier si les CRS sont différent
    if org_epsg != dest_epsg:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(org_epsg),
            QgsCoordinateReferenceSystem(dest_epsg),
            QgsProject.instance())
        # Reprojeter l'entitée
        reproject_extent = crs_transform.transform(extent)
    # Sinon les entitées n'on pas besoin d'être reprojetés
    else: reproject_extent = extent
    # Retourner l'entitée résultante
    return reproject_extent

def reprojectLayer(layer, dest_epsg):
    target_crs = QgsCoordinateReferenceSystem(f'EPSG:{dest_epsg}')
    
    # Check if reprojection is needed
    if layer.crs() == target_crs: return layer
    
    if layer.geometryType() == 0: source = "Point"
    elif layer.geometryType() == 1: source = "LineString"
    elif layer.geometryType() == 2: source = "Polygon"
    else: return None

    # Create the new vector layer with the target CRS
    new_layer = QgsVectorLayer(source, layer.name(), "memory")
    new_layer.setCrs(target_crs, True)

    transform = QgsCoordinateTransform(layer.crs(), target_crs, QgsProject.instance().transformContext())
    
    new_features = []
    # Iterate over features in the original layer
    for feature in layer.getFeatures():
        # Create a new feature with the transformed geometry
        new_feature = QgsFeature()
        geom = feature.geometry()
        geom.transform(transform)
        new_feature.setGeometry(geom)
        new_feature.setAttributes(feature.attributes())
        # Add the new feature to the new layer
        new_features.append(new_feature)

    new_layer.dataProvider().addFeatures(new_features)
    
    return new_layer

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



'''
    Fonction qui valide si une couche existe dans le projet.
    Entrée:
        layer_name (str) = Nom de la couche
        fields_name (list of str) = Nom des champs que la couche doit contenir
        geom_type (int) = Le type de géometrie de la couche
'''
def validateLayer (layer_name, fields_name=[], geom_type=None):
    # Vérifier pour chaque couche avec le même nom laquel est la bonne
    for layer in QgsProject.instance().mapLayersByName(layer_name):
        if layer.type() == 0:
            if not geom_type or layer.geometryType() == geom_type:
                # Vérifier si le champs se retrouve dans la couche
                liste_fields = [field.name() for field in layer.fields()]
                if set(fields_name).issubset(liste_fields):
                    # Succesful
                    return layer
    # Not Succesful
    return None 

def isLayerInGeopackage(geopackage, layer_name):
    if not os.path.exists(geopackage): return False
    source = f'{geopackage}|subset=SELECT * FROM gpkg_contents WHERE "table_name" LIKE \'{layer_name}\''
    for i in QgsVectorLayer(source, "names", "ogr").getFeatures(): return True
    
    return False


"""
    Retrieves the dimensions (height and width) of paper sizes based on their name.

    Paramètres:
        paper_name (str): The name of the paper size, such as 'A4' or 'ANSI A'.
        unit (str, optional): The unit of measurement for the dimensions.
            Supported values are 'mm' (millimeters), 'cm' (centimeters), and 'in' (inches).
            Defaults to 'mm'.

    Returns:
        tuple: A tuple containing the height and width of the paper size in the specified unit.

    Raises:
        ValueError: If an invalid unit is provided.

"""
def getPageFormat(paper_name, unit='mm'):
    paper_sizes = {
        # ANSI sizes
        'ANSI A': (215.9, 279.4),
        'ANSI B': (279.4, 431.8),
        'ANSI C': (431.8, 558.8),
        'ANSI D': (558.8, 863.6),
        'ANSI E': (863.6, 1117.6),

        # International standard sizes
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'A7': (74, 105),
        'A8': (52, 74),
        'A9': (37, 52),
        'A10': (26, 37),
        'B0': (1000, 1414),
        'B1': (707, 1000),
        'B2': (500, 707),
        'B3': (353, 500),
        'B4': (250, 353),
        'B5': (176, 250),
        'B6': (125, 176),
        'B7': (88, 125),
        'B8': (62, 88),
        'B9': (44, 62),
        'B10': (31, 44),
        'C0': (917, 1297),
        'C1': (648, 917),
        'C2': (458, 648),
        'C3': (324, 458),
        'C4': (229, 324),
        'C5': (162, 229),
        'C6': (114, 162),
        'C7': (81, 114),
        'C8': (57, 81),
        'C9': (40, 57),
        'C10': (28, 40)
    }
    
    if paper_name in paper_sizes:
        dimensions = paper_sizes[paper_name]
        if unit == 'mm':
            return dimensions
        elif unit == 'cm':
            return tuple(dim / 10 for dim in dimensions)
        elif unit == 'in':
            return tuple(dim * 0.0393701 for dim in dimensions)
        else:
            raise ValueError("Invalid unit. Supported units are 'mm', 'cm', and 'in'.")
    else:
        return None
