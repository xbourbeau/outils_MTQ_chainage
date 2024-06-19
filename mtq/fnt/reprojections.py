# -*- coding: utf-8 -*-
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform

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

def reprojectGeometry(geom, org_epsg, dest_epsg):
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

def reprojectFeat(feat, org_epsg, dest_epsg):
    """
    Fonction qui permet de reprojeter une entitée dans un autres système de coordonnée
    
    Args:
        - feat (QgsFeatures): L'entitée à reprojeté
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
        # Reprojeter l'entitée
        feat.geometry().transform(crs_transform)
    
    # Retourner l'entitée résultante
    return feat

def reprojectFeats(feats, org_epsg, dest_epsg):
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
        # Reprojeter les entitées
        reproject_feats = [crs_transform.transform(feat) for feat in feats]
    # Sinon les entitées n'on pas besoin d'être reprojetés
    else: reproject_feats = feats
    
    # Retourner les entitées résultantes
    return reproject_feats