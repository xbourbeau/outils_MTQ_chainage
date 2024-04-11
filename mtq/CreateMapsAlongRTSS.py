import numpy as np
import os
from .format import formaterChainage
from qgis.core import (QgsLayout, QgsProject, QgsLayoutExporter, QgsVectorLayerUtils, 
    Qgis, QgsExpressionContextUtils, QgsVectorLayer, QgsField, QgsFields)
from qgis.PyQt.QtCore import QVariant
import processing

class CreateMapsAlongRTSS:

    def __init__(self, iface, geocode, nom_projet, **kargs):
        # Définir le nom du projet
        self.nom_projet = nom_projet
        # Définir le module de Géocodage
        self.geocode = geocode
        self.iface = iface
        
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
        
        self.loadInfo()
    
    def exportLayout(self, output_path):
        """ Méthode qui permet d'exporter l'atlas """
        try:
            output_file_path = os.path.join(output_path, self.nom_projet + ".pdf")
            # Définir le nom du projet dans la variable de la mise en page
            if self.getParametre("projet_name_variable"): QgsExpressionContextUtils.setLayoutVariable(self.layout, self.getParametre("projet_name_variable"), self.nom_projet)
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
            nbr_page = atlas.updateFeatures()
            # Définir l'atlas sur la première page
            generate_atlas = atlas.first()
            QgsLayoutExporter(self.layout).exportToPdf(atlas, output_file_path, QgsLayoutExporter.PdfExportSettings())
            
            self.iface.messageBar().pushMessage(
                "Exportation complétée!",
                f"{self.nom_projet} exported to '{output_path}'",
                level=Qgis.Success,
                duration=5)
        except Exception as e:
            self.iface.messageBar().pushMessage("ERROR Export:", str(e), level=Qgis.Critical, duration=5)
        
    def getParametre(self, name): return self.param.get(name, None)
    def getScale(self): return self.getParametre("page_scale")
    def getOverlap(self): return self.getParametre("page_overlap")
    def getOffset(self): return self.getParametre("first_page_offset")
    def getAtlasMapName(self): return self.getParametre("main_atlas_map_name")
    
    def loadInfo(self):
        self.layout = QgsProject.instance().layoutManager().layoutByName(self.getParametre("layout_name"))
        size = self.layout.itemById(self.getAtlasMapName()).sizeWithUnits()
        # Hauteur (m)
        self.height = (size.height()/1_000) * self.getScale()
        # Largeur (m)
        self.width = (size.width()/1_000) * self.getScale()
        # Définir les couches
        self.layer_atlas = QgsProject.instance().mapLayersByName(self.getParametre("layer_name_atlas"))[0]
        self.layer_loc_projet = QgsProject.instance().mapLayersByName(self.getParametre("layer_name_loc"))[0]
        self.layer_chainage_1 = QgsProject.instance().mapLayersByName(self.getParametre("layer_name_chainage_niveau1"))[0]
        self.layer_chainage_2 = QgsProject.instance().mapLayersByName(self.getParametre("layer_name_chainage_niveau2"))[0]
        self.layer_chainage_3 = QgsProject.instance().mapLayersByName(self.getParametre("layer_name_chainage_niveau3"))[0]

    def setLocalisation(self, list_of_points):
        self.list_of_points = list_of_points
    
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
            for point_d, point_f in self.list_of_points:
                for page_info in self.geocode.getAtlasPages(point_d, self.width, self.height, end=point_f, overlap=self.getOverlap(), start_offset=self.getOffset()):
                    att = {i+1: val for i, val in enumerate(page_info["atts"].values())}
                    feat = QgsVectorLayerUtils.createFeature(self.layer_atlas, page_info["geom"], att)
                    self.layer_atlas.addFeature(feat)
            self.layer_atlas.commitChanges()
        except Exception as e:
            self.layer_atlas.rollBack()
            self.iface.messageBar().pushMessage("ERROR on Update layer atlas", str(e), level=Qgis.Critical, duration=5)
            return False
        return True
    
    def updateChainage(self, layer, interval):
        """ Méthode qui permet de mettre à jour les point de chainages """
        try:
            layer.startEditing()
            # Éffacer les anciennes valeurs
            layer.deleteFeatures([feat.id() for feat in layer.getFeatures()])
            for point_d, point_f in self.list_of_points:
                feat_rtss = self.geocode.getRTSS(point_d.getRTSS())
                # Nombre de point à créer sur le RTSS
                longeur_ajuster = int(point_f.getChainage()-(point_f.getChainage()%interval))
                # Parcourire chaque interval du RTSS
                for chainage in np.arange(point_d.getChainage(), longeur_ajuster+interval, interval):
                    point_chainage = feat_rtss.getPointFromChainage(chainage)
                    att = {1:feat_rtss.getRTSS(), 2:float(chainage), 3:formaterChainage(chainage), 4:feat_rtss.getAngleAtChainage(chainage)}
                    layer.addFeature(QgsVectorLayerUtils.createFeature(layer, point_chainage, att))
                    
                if point_f.getChainage() != longeur_ajuster:
                    point_chainage = feat_rtss.getPointFromChainage(point_f.getChainage())
                    att = {1:feat_rtss.getRTSS(), 2:float(point_f.getChainage()), 3:point_f.getChainage(True), 4:feat_rtss.getAngleAtChainage(point_f.getChainage())}
                    layer.addFeature(QgsVectorLayerUtils.createFeature(layer, point_chainage, att))
            layer.commitChanges()
        except Exception as e:
            layer.rollBack()
            self.iface.messageBar().pushMessage("ERROR on Update layer chainage", str(e), level=Qgis.Critical, duration=5)
            return False
        return True
    
    def updateChainageNiveau1(self): return self.updateChainage(self.layer_chainage_1, self.getParametre("interval_chainage_niveau1"))
    def updateChainageNiveau2(self): return self.updateChainage(self.layer_chainage_2, self.getParametre("interval_chainage_niveau2"))
    def updateChainageNiveau3(self): return self.updateChainage(self.layer_chainage_3, self.getParametre("interval_chainage_niveau3"))

    def updateLocalisation(self):
        """ Méthode qui permet de mettre à jour la localisation du projet """
        try:
            self.layer_loc_projet.startEditing()
            # Éffacer les anciennes valeurs
            self.layer_loc_projet.deleteFeatures([feat.id() for feat in self.layer_loc_projet.getFeatures()])
            for point_d, point_f in self.list_of_points:
                geom = self.geocode.geocoder(point_d.getRTSS(), point_d.getChainage(), chainage_f=point_f.getChainage())
                self.layer_loc_projet.addFeature(QgsVectorLayerUtils.createFeature(self.layer_loc_projet, geom, {1:self.nom_projet}))
            self.layer_loc_projet.commitChanges()
        except Exception as e:
            self.layer_loc_projet.rollBack()
            self.iface.messageBar().pushMessage("ERROR on Update layer localisation", str(e), level=Qgis.Critical, duration=5)
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














