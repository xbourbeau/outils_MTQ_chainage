# -*- coding: utf-8 -*-
import pandas as pd
import os
from typing import Union, Dict
from qgis.core import QgsProject, QgsApplication
from ..region.Province import Province
from ..param import DEFAULT_LAYER_REFERENCE, DEFAULT_AUTHID, C_PROV, C_SOURCE
from .LoadLayers import LoadLayers
from .LayerMTQ import LayerMTQ
from .GeopackageLayerMTQ import GeopackageLayerMTQ
from .WFSLayerMTQ import WFSLayerMTQ


class LayerManager:
    """ Objet qui permet de gérer des couches qui sont souvent utilisées. """
    
    def __init__(self, iface=None, layer_reference=None, authid=None, code_dt=None, code_cs=None):
        """
        Args:
            - iface: iface de QGIS
            - code_dt (int): Le code de la DT par défaut pour les filtres de couche
            - code_cs (int): Le code du CS par défaut pour les filtres de couche
        """
        self.iface = iface
        # DataFrame (vide) contenant tous les informations des couches
        self.layers:Dict[str,Union[LayerMTQ, WFSLayerMTQ, GeopackageLayerMTQ]] = {}
        if not layer_reference is None: self.loadData(layer_reference)
        # Authentifiaction ID à utiliser pour les connextions aux services web
        self.setAuthId(authid)
        # Class de gestion des limites administrative
        self.quebec = Province.fromMemory()
        # Définir un paramètre de DT
        self.setDT(code_dt)
        # Définir un paramètre de CS
        self.setCS(code_cs)
    
    @classmethod
    def fromProject(cls, iface=None, code_dt=90, code_cs=None):
        """
        Constructeur avec le nom de la couche des RTSS dans le projet courrant
        
        Args:
            - iface: iface de QGIS
            - excel_file (str): Le chemin du Excel des couches à importer
            - code_dt (int): Le code de la DT par défaut pour les filtres de couche
            - code_cs (int): Le code du CS par défaut pour les filtres de couche
        """
        return cls(
            iface=iface,
            layer_reference=DEFAULT_LAYER_REFERENCE,
            authid=DEFAULT_AUTHID,
            code_dt=code_dt,
            code_cs=code_cs)

    def __str__(self): return f"LayerManager ({len(self)} layers)"
    
    def __repr__(self): return f"LayerManager ({len(self)} layers)"

    def __len__(self): return len(self.layers)

    def __iter__ (self): return self.layers.__iter__()

    def __contains__(self, key:str): return key in self.layers

    def __getitem__(self, key): 
        try: return self.layers[key]
        except: raise KeyError(f"Le RTSS ({key}) n'est pas une couche dans le LayerManager")

    def addLayer(self, layer_name, layer_info:pd.Series):
        """ 
        Méthode qui permet d'ajouter une couche à l'index
        
        Args:
            - layer_name (str): Le nom unique de la couche
            - layer_info (Pandas Series): Une series Pandas contenant les informations de la couche
        """
        if layer_name in self: raise ValueError(f"Le nom {layer_name} est déjà dans l'index des couches")
        # Créer la couche
        if layer_info[C_PROV] == "ogr": 
            if os.path.splitext(layer_info[C_SOURCE].split("|")[0])[1] == ".gpkg":
                layer = GeopackageLayerMTQ.fromPDSerie(layer_name, layer_info)
            else: layer = LayerMTQ.fromPDSerie(layer_name, layer_info)
        else: layer = WFSLayerMTQ.fromPDSerie(layer_name, layer_info)
        # Ajouter la couche au dictionnaire des couches
        self.layers[layer_name] = layer

    def addLayerToMap(self, layer_name, use_dt=True, use_cs=False, use_style=True, **kwargs):
        """
        Méthode qui permet d'ajouter une couche au projet à partir d'un QgsTask.

        Args: 
            - task_load_layer (QgsTask): La tache avec la couche charger 
            - layer_info (dict): Les infos de la couche
            - use_style (bool/str): Le style de la couche a ajouter 
        """
        layer = self.get(layer_name)
        if layer is None: return None
        dt = self.getDT(use_dt) if use_dt else None
        cs = self.getCS(use_cs, dt) if use_cs else None
        layer.show(self.iface, use_style=use_style, authid=self.authid, dt=dt, cs=cs, **kwargs)

    def addLayersToMap(self, layer_names:list[str], use_dt=True, use_cs=False, use_style=True, **kwargs):
        """
        Méthode qui permet d'ajouter une couche au projet à partir d'un QgsTask.

        Args: 
            - task_load_layer (QgsTask): La tache avec la couche charger 
            - layer_info (dict): Les infos de la couche
            - use_style (bool/str): Le style de la couche a ajouter 
        """
        dt = self.getDT(use_dt) if use_dt else None
        cs = self.getCS(use_cs, dt) if use_cs else None
        layers, styles = {}, {}
        for layer_name in layer_names:
            layer = self.get(layer_name)
            if layer is None: continue
            layers[layer_name] = layer
            if use_style is True: styles[layer_name] = layer.getStyle(use_style)
        
        def addLayersToMapFromTask(self, task:LoadLayers, styles={}):
            for name, layer, in task.getLayers().items():
                # Ajouter la couche au projet
                map_layer = QgsProject.instance().addMapLayer(layer)
                
                # Définir un style si spécifié
                if name in  styles: map_layer.loadNamedStyle(styles[name])
                if self.iface: self.iface.layerTreeView().refreshLayerSymbology(map_layer.id())
        
        task_load_layer = LoadLayers(layers, authid=self.authid, dt=dt, cs=cs, **kwargs)
        # Ajouter la tâche
        task_load_layer.taskCompleted.connect(lambda: addLayersToMapFromTask(self, task_load_layer, styles))
        QgsApplication.taskManager().addTask(task_load_layer)

    def exportToCSV(self, csv):
        """ Methode to export all layers info to a CSV """
        self.layers.to_csv(csv, index=True)
    
    def get(self, layer_name):
        """
        Permet de retourner l'objet LayerMTQ de la couche
        Retourne None si aucune couche n'est trouvé
        """
        return self.layers.get(layer_name, None)

    def getCS(self, value=None, use_dt=None):
        if use_dt is True: use_dt = self.getDT()
        if value is True: return self.cs
        else: return self.quebec.getCS(value, dt=use_dt)
          
    def getDataProvider(self, layer_name):
        layer = self.get(layer_name)
        if layer is None: return None
        return layer.dataProvider()

    def getDataSource(self, layer_name, epsg=None, **kwargs):
        """ Permet de retourner le text du dataSource d'une couche """
        layer = self.get(layer_name)
        if layer is None: return None
        return layer.dataSource(authid=self.authid, epsg=epsg, **kwargs)

    def getDefaultStyle(self, layer_name):
        layer = self.get(layer_name)
        if layer is None: return None
        return layer.defaultStyle()

    def getDT(self, value=None):
        if value is True: return self.dt
        else: return self.quebec.getDT(value)

    def getExtention(self, layer_name):
        layer = self.get(layer_name)
        if layer is None: return None
        return layer.fileExtention()
    
    def getLayer(self, layer_name, use_dt=True, use_cs=False, **kwargs):
        """ 
        Méthode qui permet de charger une couche et de retourner le QgsVectorLayer de la couche.
        
        Args:
            - layer_name (str): Le nom de la couche dans l'index des couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
            - epsg (int): Code EPSG d'une projection utiliser si disponible
            - load_layer (bool): Conserver la couche en mémoire pour éviter de la recharger
        """
        layer = self.get(layer_name)
        if layer is None: return None
        dt = self.getDT(use_dt) if use_dt else None
        cs = self.getCS(use_cs, dt) if use_cs else None
        #TODO: Vérifier que la couche est valide!
        # Définir la source de la couche
        return layer.asVectorLayer(authid=self.authid, dt=dt, cs=cs, **kwargs)
    
    def getLayersTask(self, layers_names, use_dt=True, use_cs=False, **kwargs):
        """
        Méthode qui permet créer une QgsTask pour charger plusieurs couches
        
        Args:
            - layers_names (list): Les noms des couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
            - epsg (int): Code EPSG d'une projection utiliser si disponible
        """
        layers = {}
        for name in layers_names:
            layer = self.get(name)
            if layer is None: continue

            dt = self.getDT(use_dt) if use_dt else None
            cs = self.getCS(use_cs, dt) if use_cs else None
            # Définir la source de la couche
            data_source = layer.dataSource(authid=self.authid, dt=dt, cs=cs, **kwargs)
            layers[name] = {"data_source": data_source, "provider": layer.dataProvider()}
        # Retourner la Task 
        return LoadLayers(layers)

    def getLayerIdField(self, layer_name):
        """ Méthode qui permet de retourner le nom du champs de l'identifiant de la couche"""
        try: return self.get(layer_name).key_field_name
        except: return None
        
    def getLayerDTField(self, layer_name):
        """ Méthode qui permet de retourner le nom du champs contenant la DT dans la couche """
        try: return self.get(layer_name).dt_field_name
        except: return None
        
    def getLayerCSField(self, layer_name):
        """ Méthode qui permet de retourner le nom du champs contenant le CS dans la couche """
        try: return self.get(layer_name).cs_field_name
        except: return None
    
    def getLayerRequests(self, layer_name):
        """ Méthode qui retourn la liste des noms de requête """
        try: return list(self.get(layer_name).requests().keys())
        except: return None
    
    def getLayerStyles(self, layer_name):
        """ Méthode qui retourn la liste des noms de requête """
        try: return list(self.get(layer_name).styles().keys())
        except: return None
        
    def getLayerInProject(self, layer_name, use_name=True, use_source=True):
        """
        Méthode qui retourne une liste de QgsMapLayer qui sont dans le projet selon la source et/ou le nom de la couche
        
        Args:
            - layer_name (str): Le nom de la couche dans l'index
            - use_name (bool): Utiliser le nom de la couche comme recherche
            - use_source (bool): Utiliser la source de la couche comme recherche
        """ 
        map_layers_list = []
        layer = self.get(layer_name)
        if layer is None: return map_layers_list
        # Parcourir les couches de l'instance du projet
        for layer_id in QgsProject.instance().mapLayers():
            # La référence de la couche courant dans la boucle
            map_layer = QgsProject.instance().mapLayer(layer_id)
            # Sources de la couche courant dans la boucle
            data = map_layer.dataProvider()
            # Vérifier s'il faut vérifier par nom et si le nom des couches sont indentique
            if use_name and layer_name==map_layer.name(): map_layers_list.append(map_layer)
            # Vérifier s'il faut vérifier par source et si le type de couche sont indentique
            elif use_source and layer.dataProvider() == data.name().lower():
                if layer.dataProvider() == 'ogr':
                    # Retirer la couche du projet si les sources OGR sont indentique
                    if layer.source() == data.dataSourceUri().split('|')[0]: map_layers_list.append(map_layer)
                elif layer.dataProvider() == 'wfs':
                    # Vérifier si le nom de la source WFS et le lien vers le WFS sont indentique 
                    if layer.typename() == data.uri().param("typename"): map_layers_list.append(map_layer)
        return map_layers_list
    
    def getTags(self, layer_name):
        """ Méthodes qui permet de retourner la liste des tags de la couche """
        if layer_name in self.layers: return self.layers[layer_name].tags()
        else: return []
    
    def getTerritoire(self, use_dt=True):
        """
        Méthode qui permet de retourner le module du territoire utilisé par le gestionnaire de couche 
        
        Args:
            - use_dt (bool): Retourner seulement la DT
        """
        if use_dt and self.hasDT(): return self.dt
        else: return self.quebec
    
    def hasCS(self): return self.cs is not None
    
    def hasDT(self): return self.dt is not None
    
    def isLayerInProject(self, layer_name, use_name=True, use_source=False):
        """
        Méthode qui permet de vérifier si une couche est dans le projet.
        La recherche peut ce faire par nom de la couche et/ou la source de la cocuhe

        Args:
            - layer_name (str): Nom de la couche dans l'index
            - use_name (bool): Utiliser le nom de la couche comme recherche
            - use_source (bool): Utiliser la source de la couche comme recherche 
        """
        return len(self.getLayerInProject(layer_name, use_name=use_name, use_source=use_source)) > 0
    
    def loadData(self, file):
        """
        Méthode qui permet de charger des informations sur des couches à partir d'un
        Excel ou d'un CSV.

        Args:
            - file (str): Le chemin vers le fichier (*.csv ou *.xlsx) à charger
        """
        # Verifier si le chemin vers le fichier est valide
        if not os.path.exists(file): raise Exception(f"Le fichier ({file}) est introuvable")
        # Vérifier que le fichier a une extention
        if not "." in file: raise Exception(f"Le fichier ({file}) doit avoir une extention")
        # Définir l'extention du fichier 
        root, extension = os.path.splitext(file)
        if extension == ".csv": layers_table = pd.read_csv(file, index_col=0)
        elif extension == ".xlsx": layers_table = pd.read_excel(file, index_col=0)
        else: raise Exception(f"Le fichier ({file}) doit être un Document .csv ou .xlsx")
        
        # ---------- Convertir les champs ----------
        layers_table.fillna("")
        # Parcourir chaque couche du tableau
        for layer_name in layers_table.index:
            # Vérifier que la couche n'est pas déjà dans le dictionnaire
            if layer_name in self.layers: continue
            # Ajouter la couche au module
            self.addLayer(layer_name, layers_table.loc[layer_name])
    
    def loadFromCSV(self, csv):
        """ Methode to load all layers info in a Pandas DataFrame from CSV"""
        self.loadData(csv)
        
    def loadFromExcel(self, excel_file):
        """ Methode to load all layers info in a Pandas DataFrame from Excel"""
        self.loadData(excel_file)
    
    def removeLayerFromProject(self, layer_name, use_name=True, use_source=False):
        """ Méthode qui permet de retirer une couche, qui se trouve dans un QgsProject """
        for layer in self.getLayerInProject(layer_name, use_name=use_name, use_source=use_source):
            QgsProject.instance().removeMapLayer(layer.id())
    
    def searcheLayers(self, recherche="", use_tags=True):
        """ 
        Méthode qui permet de retourner les couches dans la gestionnaire de couche 
        selon un text de recherche.
        
        Args:
            - recherche (str): Texte qui permet de rechercher du text dans la liste des couches
            - use_tags (bool): Utiliser les tags de la couche pour la recherche
        """
        # Retrouner toutes les couches si aucune recherche est spécifié 
        if recherche == "": return list(self.layers.keys())
        layer_names = []
        # Parcourir toute les couches
        for layer_name in self.layers.keys():
            list_of_text_search = [layer_name]
            if use_tags: list_of_text_search += self.getTags(layer_name)
            for text in list_of_text_search: 
                if recherche.lower() == text.lower()[:len(recherche)]:
                    layer_names.append(layer_name)
                    break
                if len(recherche) > 1 and recherche.lower() in text.lower():
                    layer_names.append(layer_name)
                    break
        return layer_names

    def setAuthId(self, authid):
        """ Méthode qui permet de définir le authentification id à utiliser """
        self.authid = authid
    
    def setCS(self, code_cs):
        """ Méthode qui permet de définir un CS par défault """
        self.cs = self.quebec.getCS(code_cs, self.dt)
                
    def setDT(self, code_dt):
        """ Méthode qui permet de définir une DT par défault """
        self.dt = self.quebec.getDT(code_dt)
