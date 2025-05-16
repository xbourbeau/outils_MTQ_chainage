# -*- coding: utf-8 -*-
from qgis.core import (
    QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsGeometry, QgsPointXY, QgsFeature)

def reprojectExtent(extent, org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter un étendu dans un autres système de coordonnée
    
    Args:
        - feat (QgsRectangle) = L'extent à reprojeté
        - org_epsg (int) = Code EPSG du CRS de l'entitée
        - dest_epsg (int) = Code EPSG du CRS de l'entitée résultante
        
    Return:
        - reproject_extent (QgsRectangle) = L'extent reprojeté
    """
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    # Vérifier si les CRS sont différent
    if org_epsg != dest_epsg:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance().transformContext())
        # Reprojeter l'entitée
        reproject_extent = crs_transform.transformBoundingBox(extent)
    # Sinon les entitées n'on pas besoin d'être reprojetés
    else: reproject_extent = extent
    # Retourner l'entitée résultante
    return reproject_extent

def reprojectGeometry(geom:QgsGeometry, org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter une géometrie dans un autres système de coordonnée
    
    Args:
        - geom (QgsGeometry): La geometrie à reprojeté
        - org_epsg (int): Code EPSG du CRS de l'entitée
        - dest_epsg (int): Code EPSG du CRS de l'entitée résultante
        
    Sortie:
        - geom (QgsGeometry): La geometrie reprojeté
    """
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    # Vérifier si les CRS sont différent
    if org_epsg != dest_epsg:
        if not crsDest.isValid() or not crsSrc.isValid(): return False
        # Reprojeter l'entitée avec la méthode de transformation entre les deux CRS
        geom.transform(QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance()))
    
    # Retourner l'entitée résultante
    return geom

def reprojectPoint(point:QgsPointXY, org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter un point dans un autres système de coordonnée
    
    Args:
        - point (QgsPointXY): Le point à reprojeté
        - org_epsg (int): Code EPSG du CRS du point
        - dest_epsg (int): Code EPSG du CRS du point résultante
        
    Sortie:
        - reproject_point (QgsPointXY): Le point reprojeté
    """
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    
    # Vérifier si les CRS sont différent
    if crsSrc != crsDest:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        # Reprojeter le point
        point = crs_transform.transform(point)
    
    # Retourner le point résultante
    return point

def reprojectPoints(points:list[QgsPointXY], org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter un point dans un autres système de coordonnée
    
    Args:
        - point (list of QgsPointXY): Liste de points à reprojeté
        - org_epsg (int): Code EPSG du CRS des points
        - dest_epsg (int): Code EPSG du CRS des point résultante
        
    Sortie:
        - reproject_points (list of QgsPointXY): Les points reprojetés
    """
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    
    # Vérifier si les CRS sont différent
    if crsSrc != crsDest:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        # Reprojeter les points
        reproject_points = [crs_transform.transform(pt) for pt in points]
        
    # Retourner les points résultante
    return reproject_points

def reprojectFeat(feat:QgsFeature, org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter une entitée dans un autres système de coordonnée
    
    Args:
        - feat (QgsFeature): L'entitée à reprojeté
        - org_epsg (int): Code EPSG du CRS de l'entitée
        - dest_epsg (int): Code EPSG du CRS de l'entitée résultante
        
    Sortie:
        - reproject_feat (QgsFeatures): L'entitée reprojeté
    """
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    
    # Vérifier si les CRS sont différent
    if crsSrc != crsDest:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        geom = feat.geometry()
        geom.transform(crs_transform)
        feat.setGeometry(geom)
    
    # Retourner l'entitée résultante
    return feat

def reprojectFeats(feats:list[QgsFeature], org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter une entitée dans un autres système de coordonnée
    
    Args:
        - feat (List of QgsFeatures): Liste des entitée à reprojeté
        - org_epsg (int): Code EPSG du CRS des entitées
        - dest_epsg (int): Code EPSG du CRS des entitées résultantes
        
    Sortie:
        - reproject_feats (List of QgsFeatures): Liste d'entitée reprojeté
    """
    # Instancier les CRS à partir des codes EPSG
    crsDest = QgsCoordinateReferenceSystem(dest_epsg)
    crsSrc = QgsCoordinateReferenceSystem(org_epsg)
    
    # Vérifier si les CRS sont différent
    if crsSrc != crsDest:
        # Instancier la méthode de transformation entre les deux CRS
        crs_transform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        reproject_feats = []
        for feat in feats:
            geom = feat.geometry()
            geom.transform(crs_transform)
            feat.setGeometry(geom)
            reproject_feats.append(feat)
    # Sinon les entitées n'on pas besoin d'être reprojetés
    else: reproject_feats = feats
    # Retourner les entitées résultantes
    return reproject_feats