import numpy as np
import os
from qgis.core import (QgsProject, QgsLayoutExporter, QgsVectorLayerUtils, 
    QgsExpressionContextUtils, QgsVectorLayer, QgsField, QgsFields, QgsMapLayer)
from qgis.PyQt.QtCore import QVariant
import processing
from typing import Union
from .geomapping.imports import *

class AtlasRTSS:
    """
    Un module qui permet d'intéragir avec un projet QGIS pour créer des cartes 
    d'un atlas le long d'un RTSS. Le projet doit être créer à partir du modèle de carte.
    """

    def __init__(self, project_name:str, project_file:str, geocode:Geocodage, **kargs):
        """
        Instanciation de l'objet CreateMapsAlongRTSS

        Args:
            - project_name (str): Le nom à donnée au projet
            - project_file (str): Le chemin vers le projet QGIS contenant les cartes
            - geocode (Geocodage): Le module de Geocodage
            - kargs: Toutes autres paramètres du module
        """
        # Définir le nom du projet 
        self.project_name = project_name
        # Create a new instance of QgsProject
        self.project_instance = QgsProject()
        # Load the project file into the new project instance
        self.project_instance.read(project_file)
        
        # Définir le module de Géocodage
        self.geocode = geocode
        
        # Enumeration des paramètres
        self.param = {
            # Échelle des pages de l'atlas
            "page_scale":1000,
            # Pourcentage de la page de l'atlas qui doivent se superposer
            "page_overlap":20,
            # Pourcentage de la première page qui doit être décaler pour être visible
            "first_page_offset":10,
            # Distance représentant la marge autour de la couche des pages dans la carte de localisation
            "loc_buffer_distance":500,
            # Interval des chainages (espacement principal)
            "interval_chainage_niveau1":100,
            # Interval des chainages (espacement niveau 2)
            "interval_chainage_niveau2":None,
            # Interval des chainages (espacement niveau 3)
            "interval_chainage_niveau3":None,
            # L'identifiant de la carte de localisation dans la mise en page
            "loc_map_name":"Localisation",
            # Ratio minimum de (hauteur/largeur) de l'étendu de la couche des pages pour néssésiter une rotation
            "loc_map_min_ratio":1.3,
            # Nom de la mise en page
            "layout_name":"Cartes du marquage longitudinale",
            # Nom de la variable contenant le titre dans la mise en page
            "projet_name_variable": "projet_name",
            # Nom de la couche dans le projet contenant les page de l'atlas
            "layer_name_atlas": "Atlas_pages",
            # Nom de la couche dans le projet contenant la localisation de l'atlas
            "layer_name_loc": "localisation_projet",
            # Nom de la couche dans le projet contenant les points de chainages niveau 1
            "layer_name_chainage_niveau1": "Points_chainage_niveau1",
            # Nom de la couche dans le projet contenant les points de chainages niveau 2
            "layer_name_chainage_niveau2": "Points_chainage_niveau2",
            # Nom de la couche dans le projet contenant les points de chainages niveau 3
            "layer_name_chainage_niveau3": "Points_chainage_niveau3",
            # L'identifiant de la carte de l'atlas dans la mise en page
            "main_atlas_map_name": "Carte 1"}
        # Modififer les paramètres si besoin
        self.setParametres(kargs, reload_info=False)
        # Charger les informations nécéssaire
        self.loadInfo()
    
    def exportLayout(self, output_folder:str):
        """
        Méthode qui permet d'exporter l'atlas en PDF
        
        Args:
            - output_folder (str): Le dossier de la carte en sortie
        """
        try:
            # Vérifier que le dossier est valide 
            if not os.path.exists(output_folder): raise Exception(f"Folder ({output_folder}) doesnt exist")
            # Définir le fichier pdf en sortie
            output_file = os.path.join(output_folder, self.project_name + ".pdf")
            # Définir le nom du projet dans la variable de la mise en page
            if self.getParametre("projet_name_variable"): 
                QgsExpressionContextUtils.setLayoutVariable(self.layout, self.getParametre("projet_name_variable"), self.project_name)
            # Get Atlas from layout
            atlas = self.layout.atlas()

            # Définir l'étendu de la carte de localisation
            project_extent = self.layer_atlas.extent().buffered(self.getParametre("loc_buffer_distance"))
            loc_map = self.layout.itemById(self.getParametre("loc_map_name"))
            loc_map.zoomToExtent(project_extent)
            loc_map_size = loc_map.sizeWithUnits()
            if project_extent.height()/project_extent.width() > self.getParametre("loc_map_min_ratio"):
                loc_map.setMapRotation(90)
                scale = max([project_extent.height()/(loc_map_size.width()/1_000), project_extent.width()/(loc_map_size.height()/1_000)])
                loc_map.setScale(scale)
            else: loc_map.setMapRotation(0)
            # Activer la génération de l'atlas 
            atlas.updateFeatures()
            # Définir l'atlas sur la première page
            atlas.first()
            # Exporter l'atlas en PDF
            QgsLayoutExporter(self.layout).exportToPdf(atlas, output_file, QgsLayoutExporter.PdfExportSettings())
        except Exception as e:
            print(e)
            pass
        
    def getParametre(self, name): return self.param.get(name, None)
    def getScale(self): return self.getParametre("page_scale")
    def getOverlap(self): return self.getParametre("page_overlap")
    def getOffset(self): return self.getParametre("first_page_offset")
    def getAtlasMapName(self): return self.getParametre("main_atlas_map_name")
    
    def loadInfo(self):
        """
        Permet de créer les références que le module à besoin dans le projet
        """
        # Référence de la carte
        self.layout = self.project_instance.layoutManager().layoutByName(self.getParametre("layout_name"))
        # Définir la taille de l'atlas
        size = self.layout.itemById(self.getAtlasMapName()).sizeWithUnits()
        # Hauteur (m)
        self.height = (size.height()/1_000) * self.getScale()
        # Largeur (m)
        self.width = (size.width()/1_000) * self.getScale()
        # Couche contenant les pages d'atlas
        self.layer_atlas = self.project_instance.mapLayersByName(self.getParametre("layer_name_atlas"))[0]
        # Couche de la localisation du projet de l'atlas
        self.layer_loc_projet = self.project_instance.mapLayersByName(self.getParametre("layer_name_loc"))[0]
        # Couches des chainages
        self.layer_chainage_1 = self.project_instance.mapLayersByName(self.getParametre("layer_name_chainage_niveau1"))[0]
        self.layer_chainage_2 = self.project_instance.mapLayersByName(self.getParametre("layer_name_chainage_niveau2"))[0]
        self.layer_chainage_3 = self.project_instance.mapLayersByName(self.getParametre("layer_name_chainage_niveau3"))[0]

    def setLocalisation(self, list_of_lines:list[LineRTSS]):
        self.list_of_lines = list_of_lines
    
    def setParametre(self, name, val, reload_info=True):
        if not name in self.param: return False
        self.param[name] = val
        if reload_info: self.loadInfo()
        return True
        
    def setParametres(self, dict_params, reload_info=True):
        for name, value in dict_params.items(): self.setParametre(name, value, reload_info=False)
        if reload_info: self.loadInfo()
    
    def updatePages(self):
        """ Méthode qui permet de mettre à jour les pages de l'atlas """
        try:
            self.layer_atlas.startEditing()
            # Éffacer les anciennes valeurs
            self.layer_atlas.deleteFeatures([feat.id() for feat in self.layer_atlas.getFeatures()])
            for line in self.list_of_lines:
                for page_info in self.geocode.getAtlasPages(
                        line,
                        self.width,
                        self.height,
                        overlap=self.getOverlap(),
                        start_offset=self.getOffset()):
                    att = {i+1: val for i, val in enumerate(page_info["atts"].values())}
                    # Convertir l'objet RTSS en Texte
                    att[1] = str(att[1])
                    # Convertir les objets Chainage en entier
                    att[2] = int(att[2])
                    att[3] = int(att[3])
                    feat = QgsVectorLayerUtils.createFeature(self.layer_atlas, page_info["geom"], att)
                    self.layer_atlas.addFeature(feat)
            self.layer_atlas.commitChanges()
        except Exception as e:
            self.layer_atlas.rollBack()
            return False
        return True
    
    def updateChainage(self, layer:Union[QgsMapLayer, QgsVectorLayer], interval):
        """ Méthode qui permet de mettre à jour les point de chainages """
        try:
            layer.startEditing()
            # Éffacer les anciennes valeurs
            layer.deleteFeatures([feat.id() for feat in layer.getFeatures()])
            for line in self.list_of_lines:
                start_point, end_point = line.startPoint(), line.endPoint()
                feat_rtss = self.geocode.get(line.listRTSS()[0])
                # Nombre de point à créer sur le RTSS
                longeur_ajuster = int(end_point.getChainage()-(end_point.getChainage()%interval))
                # Parcourire chaque interval du RTSS
                for chainage in np.arange(start_point.getChainage(), longeur_ajuster+interval, interval):
                    point_chainage = feat_rtss.geocoderPointFromChainage(chainage)
                    att = {1:str(feat_rtss.getRTSS()),
                           2:float(chainage),
                           3:Chainage(chainage).value(True),
                           4:feat_rtss.getAngleAtChainage(chainage)}
                    layer.addFeature(QgsVectorLayerUtils.createFeature(layer, point_chainage, att))
                    
                if end_point.getChainage() != longeur_ajuster:
                    point_chainage = feat_rtss.geocoderPointFromChainage(chainage)
                    att = {1:str(feat_rtss.getRTSS()),
                           2:float(end_point.getChainage()),
                           3:end_point.getChainage().value(True),
                           4:feat_rtss.getAngleAtChainage(end_point.getChainage())}
                    layer.addFeature(QgsVectorLayerUtils.createFeature(layer, point_chainage, att))
            layer.commitChanges()
        except Exception as e:
            layer.rollBack()
            return False
        return True
    
    def updateChainageNiveau1(self): return self.updateChainage(self.layer_chainage_1, self.getParametre("interval_chainage_niveau1"))
    def updateChainageNiveau2(self): return self.updateChainage(self.layer_chainage_2, self.getParametre("interval_chainage_niveau2"))
    def updateChainageNiveau3(self): return self.updateChainage(self.layer_chainage_3, self.getParametre("interval_chainage_niveau3"))

    def updateLocalisation(self):
        """ Méthode qui permet de mettre à jour la couche de localisation du projet """
        try:
            self.layer_loc_projet.startEditing()
            # Éffacer les anciennes valeurs
            self.layer_loc_projet.deleteFeatures([feat.id() for feat in self.layer_loc_projet.getFeatures()])
            for line in self.list_of_lines:
                self.layer_loc_projet.addFeature(QgsVectorLayerUtils.createFeature(
                    self.layer_loc_projet, self.geocode.geocoderLine(line), {1:self.project_name}))
            self.layer_loc_projet.commitChanges()
        except Exception as e:
            self.layer_loc_projet.rollBack()
            return False
        return True
            
    def updateLayers(self):
        """ Méthode qui permet de mettre a jour les 3 couches """
        if not self.updatePages(): return False
        if self.getParametre("interval_chainage_niveau1"): 
            if not self.updateChainageNiveau1(): return False
        if self.getParametre("interval_chainage_niveau2"): 
            if not self.updateChainageNiveau2(): return False
        if self.getParametre("interval_chainage_niveau3"): 
            if not self.updateChainageNiveau3(): return False
        if not self.updateLocalisation(): return False


def createAtlasGeopackage(output_path):
    geopackage_path = os.path.join(output_path, "Data_RTSS_Atlas.gpkg")
    
    layer_atlas = QgsVectorLayer("Polygon?crs=epsg:3798", "atlas_pages", "memory")
    layer_loc_projet = QgsVectorLayer("LineString?crs=epsg:3798", "localisation_projet", "memory")
    layer_chainage = QgsVectorLayer("Point?crs=epsg:3798", "point_chainage", "memory")
    
    # Define fields for each layer
    layer_atlas_fields = [("rtss", QVariant.String), ("chainage_d", QVariant.Double), ("chainage_f", QVariant.Double), ("angle", QVariant.Double)]
    layer_loc_projet_fields = [("nom", QVariant.String)]
    layer_chainage_fields = [("rtss", QVariant.String), ("chainage", QVariant.Double), ("chainage_formater", QVariant.String), ("angle", QVariant.Double)]
    
    for layer, fields in ((layer_atlas, layer_atlas_fields), (layer_loc_projet, layer_loc_projet_fields), (layer_chainage, layer_chainage_fields)):
        # Add fields to the layer
        layer_fields = QgsFields()
        for field in fields: layer_fields.append(QgsField(field[0], field[1]))
        layer.dataProvider().addAttributes(layer_fields)
        layer.updateFields()
    params = {'LAYERS': [layer_atlas, layer_loc_projet, layer_chainage],
              'OUTPUT': geopackage_path,
              'OVERWRITE': False,  # Important!
              'SAVE_STYLES': False,
              'SAVE_METADATA': False,
              'SELECTED_FEATURES_ONLY': False}
    processing.run("native:package", params)
    return True














