# -*- coding: utf-8 -*-
import pandas as pd
import os
from typing import Union, Dict
from qgis.core import QgsProject, QgsApplication, QgsVectorLayer
from ..region.Province import Province
from ..param import DEFAULT_LAYER_REFERENCE, DEFAULT_AUTHID, C_PROV, C_SOURCE
from .LoadLayers import LoadLayers
from .LayerMTQ import LayerMTQ
from .GeopackageLayerMTQ import GeopackageLayerMTQ
from .WFSLayerMTQ import WFSLayerMTQ
from .WMSLayerMTQ import WMSLayerMTQ
from ..utils import Utilitaire
from ..search.SearchEngine import SearchEngine


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
        # Définir l'engin de recherche de couche
        self.search_engine = SearchEngine()
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
        try:
            # Vérifier que la couche est unique
            if layer_name in self: raise ValueError(f"Le nom {layer_name} est déjà dans l'index des couches")
            # Vérifier si le provider est OGR
            if layer_info[C_PROV] == "ogr": 
                if os.path.splitext(layer_info[C_SOURCE].split("|")[0])[1] == ".gpkg":
                    layer = GeopackageLayerMTQ.fromPDSerie(layer_name, layer_info)
                else: layer = LayerMTQ.fromPDSerie(layer_name, layer_info)
            # Vérifier si le provider est WFS
            elif layer_info[C_PROV] == "wfs": layer = WFSLayerMTQ.fromPDSerie(layer_name, layer_info)
            # Sinon ne pas ajouter la couche
            else: return None
            # Ajouter la couche au dictionnaire des couches
            self.layers[layer_name] = layer

        # Informer l'utilisateur de l'erreur
        except Exception as e:
            if self.iface: Utilitaire.criticalMessage(self.iface, str(e), subject=f"Erreur sur la couche ({layer_name})")

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

    def clear(self):
        """ Permet de retirer toutes les références des couches du LayerManager """
        self.layers.clear()
        # Mettre à l'index de recherche
        self.updateSearchEngine()

    def exportToCSV(self, csv):
        """ Methode to export all layers info to a CSV """
        self.layers.to_csv(csv, index=True)
    
    def get(self, layer_name):
        """
        Permet de retourner l'objet LayerMTQ de la couche
        Retourne None si aucune couche n'est trouvé
        """
        return self.layers.get(layer_name, None)
    
    def getFromLayer(self, layer:QgsVectorLayer, use_name=False, use_source=True):
        """
        Permet de retourner la couche MTQ à partir d'une couche QgsVectorLayer

        Args:
            layer (QgsVectorLayer): La couche à vérifier si elle est dans le manager
            use_name (bool, optional): Utiliser le nom de la couche. Defaults to False.
            use_source (bool, optional): Utiliser la source de la couche. Defaults to True.
        """
        # Parcourir les couches de l'instance du projet
        for layer_name, layer_mtq in self.layers.items():
            # Vérifier s'il faut vérifier par nom et si le nom des couches sont indentique
            if use_name and layer_name==layer.name(): return layer_mtq
            # Vérifier s'il faut vérifier par source et si le type de couche sont indentique
            elif use_source and layer_mtq.dataProvider() == layer.dataProvider().name().lower():
                if layer_mtq.dataProvider() == 'ogr':
                    # Retourner la couche si les sources OGR sont indentique
                    if layer_mtq.hasSameSource(layer.source()): return layer_mtq
                elif layer_mtq.dataProvider() == 'wfs':
                    # Vérifier si le nom de la source WFS et le lien vers le WFS sont indentique 
                    if layer_mtq.hasSameSource(layer.dataProvider().uri()): return layer_mtq
        return None

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
        """ Permet de retourner l'extention d'une couche """
        layer = self.get(layer_name)
        if layer is None: return None
        return layer.fileExtention()
    
    def getDescription(self, layer_name):
        """ Permet de retourner la description d'une couche """
        layer = self.get(layer_name)
        if layer is None: return None
        return layer.getDescription()

    def getDisplayName(self, layer_name):
        """
        Permet de retourner l'alias d'une couche ou directement
        son nom si aucun alias est spécifié.
        """
        layer = self.get(layer_name)
        if layer is None: return None
        if layer.name(): return layer.name()
        else: return layer_name

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
    
    def isLayerInManager(self, layer:QgsVectorLayer, use_name=False, use_source=True):
        """
        Permet de vérifier si une couche est dans le LayerManager

        Args:
            layer (QgsVectorLayer): La couche à vérifier si elle est dans le manager
            use_name (bool, optional): Utiliser le nom de la couche. Defaults to False.
            use_source (bool, optional): Utiliser la source de la couche. Defaults to True.
        """
        # Parcourir les couches de l'instance du projet
        for layer_name, layer_mtq in self.layers.items():
            # Vérifier s'il faut vérifier par nom et si le nom des couches sont indentique
            if use_name and layer_name==layer.name(): return True
            # Vérifier s'il faut vérifier par source et si le type de couche sont indentique
            elif use_source and layer_mtq.dataProvider() == layer.dataProvider().name().lower():
                if layer_mtq.dataProvider() == 'ogr':
                    # Retourner la couche si les sources OGR sont indentique
                    if layer_mtq.hasSameSource(layer.source()): return True
                elif layer_mtq.dataProvider() == 'wfs':
                    # Vérifier si le nom de la source WFS et le lien vers le WFS sont indentique 
                    if layer_mtq.hasSameSource(layer.dataProvider().uri()): return True
        return False

    def getLayers(self):
        return self.layers.values()

    def layerType(self, layer_name):
        """
        Permet de retourner le type de la couche.
        Ex: ogr, wfs, gpkg

        Args:
            - layer_name (str): Nom de la couche dans l'index
        """
        layer = self.get(layer_name)
        if isinstance(layer, GeopackageLayerMTQ): return "gpkg"
        if isinstance(layer, WFSLayerMTQ): return "wfs"
        if isinstance(layer, WMSLayerMTQ): return "wms"
        if isinstance(layer, LayerMTQ): return "ogr"
        return None

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
        layers_table = layers_table.fillna("")
        # Parcourir chaque couche du tableau
        for layer_name in layers_table.index:
            # Vérifier que la couche n'est pas déjà dans le dictionnaire
            if layer_name in self.layers: continue
            # Ajouter la couche au module
            self.addLayer(layer_name, layers_table.loc[layer_name])
        # Mettre à l'index de recherche
        self.updateSearchEngine()
    
    def loadFromCSV(self, csv):
        """ Methode to load all layers info in a Pandas DataFrame from CSV"""
        self.loadData(csv)
        
    def loadFromExcel(self, excel_file):
        """ Methode to load all layers info in a Pandas DataFrame from Excel"""
        self.loadData(excel_file)
    
    def openGeocatalogue(self, layer_name):
        """
        Permet d'ouvrir la fiche vers le géocatalogue.

        Args:
            - layer_name (str): Nom de la couche dans l'index
        """
        layer = self.get(layer_name)
        if layer is None: return None
        if layer.lienGeocatalogue() != "":
            os.startfile(layer.lienGeocatalogue())

    def removeLayerFromProject(self, layer_name, use_name=True, use_source=False):
        """ Méthode qui permet de retirer une couche, qui se trouve dans un QgsProject """
        for layer in self.getLayerInProject(layer_name, use_name=use_name, use_source=use_source):
            QgsProject.instance().removeMapLayer(layer.id())
    
    def searcheLayers(self, recherche="", use_tags=True, limit=1_000):
        """ 
        Méthode qui permet de retourner les couches dans la gestionnaire de couche 
        selon un text de recherche.
        
        Args:
            - recherche (str): Texte qui permet de rechercher du text dans la liste des couches
            - use_tags (bool): ** INUTILE **
            - limit (int): Le nombre maximum de retour dans la liste
        """
        # Retrouner toutes les couches si aucune recherche est spécifié 
        if recherche == "": return list(self.layers.keys())
        # Retourner le résultat de la recherche
        return self.search_engine.search(recherche, limit=limit)

    def setAuthId(self, authid):
        """ Méthode qui permet de définir le authentification id à utiliser """
        self.authid = authid
    
    def setCS(self, code_cs):
        """ Méthode qui permet de définir un CS par défault """
        self.cs = self.quebec.getCS(code_cs, self.dt)
                
    def setDT(self, code_dt):
        """ Méthode qui permet de définir une DT par défault """
        self.dt = self.quebec.getDT(code_dt)

    def updateSearchEngine(self):
        """ Permet de mettre à jour l'index de recherche selon l'index des couches """
        # Définir un dictionnaire de recherche
        index = {layer.id(): [layer.name()] + layer.tags() for layer in self.getLayers()}
        # Mettre à jour l'engin de recherche avec l'index créer
        self.search_engine.updateSearchingIndex(index, split_word=True)