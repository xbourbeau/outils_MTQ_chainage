# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
from ast import literal_eval
from qgis.core import (QgsDataSourceUri, Qgis, QgsVectorLayer, QgsProject, 
                       QgsTask, QgsMessageLog, QgsApplication)
from .region import Province

class LayerManager:
    """ Objet qui permet de gérer des couches qui sont souvent utilisées. """
    def __init__(self, iface=None, code_dt=None, code_cs=None, deactivate_message=True):
        """
        Args:
            - iface: iface de QGIS pour afficher des messages
            - code_dt (int): Le code de la DT par défaut pour les filtres de couche
            - code_cs (int): Le code du CS par défaut pour les filtres de couche
            - deactivate_message (bool): Désactiver les messages dans QGIS
        """
        # DataFrame (vide) contenant tous les informations des couches
        self.layers = pd.DataFrame()
        # Dictionnaire des couches qui sont chargées
        self.loaded_layers = {}
        self.loaded_layers_datasources = {}
        
        # Interface courante pour l'affichage
        self.iface = iface
        # Indicteur pour afficher les messages d'erreur ou non
        self.deactivate_message = deactivate_message
        # Authentifiaction ID à utiliser pour les connextions aux services web
        self.authid = None
        
        # Class de gestion des limites administrative
        self.quebec = Province.fromMemory()
        # Définir un paramètre de DT
        self.setDT(code_dt)
        # Définir un paramètre de CS
        self.setCS(code_cs)

        # ========================== Noms des champs ==========================
        # name = Nom de la couche (doit être unique)
        self.c_name = "name"
        # alias = Nom qui apparait dans la recherche
        self.c_alias = "alias"
        # tag = Liste de mots clé séparé par des ; pour la recherche
        self.c_tag = "tag"
        # source = Le chemin pour se rendre à la couche
        self.c_source = "source"
        # provider = Le type de couche
        self.c_prov = "provider"
        # key_fields = Le nom du champs qui sert d'identifiant
        self.c_id_name = "key_fields"
        # key_fields_type = Le type du champs qui sert d'identifiant
        self.c_id_type = "key_fields_type"
        # code_dt_field = Le nom du champs qui contient un code (format text) de DT 
        self.c_dt = "code_dt_field"
        # type_code_dt_field = La réprensentation de l'identifiant de la DT. Les valeurs possibles sont (code, court, long, complet)
        self.c_type_dt = "type_code_dt_field"
        # code_cs_field = Le nom du champs qui contient un code (format text) de CS
        self.c_cs = "code_cs_field"
        # type_code_cs_field = La réprensentation de l'identifiant du CS. Les valeurs possibles sont (code, court, long, complet)
        self.c_type_cs = "type_code_cs_field"
        # requests = Un dictionnaire des requetes de la couche
        self.c_requests = "requests"
        # styles = Un dictionnaire des styles de la couche
        self.c_styles = "styles"
        # default_style = Le style par défault de la couche
        self.c_dstyle = "default_style"
        # Champs temporaire ajouter avec les extentions
        self.c_extention = "extention"
    
    @classmethod
    def fromProject(cls, iface=None, excel_file=None, code_dt=90, code_cs=None, deactivate_message=True):
        """
        Constructeur avec le nom de la couche des RTSS dans le projet courrant
        
        Args:
            - iface: iface de QGIS pour afficher des messages
            - excel_file (str): Le chemin du Excel des couches à importer
            - code_dt (int): Le code de la DT par défaut pour les filtres de couche
            - code_cs (int): Le code du CS par défaut pour les filtres de couche
            - deactivate_message (bool): Désactiver les messages dans QGIS
        """
        layer_manager = cls(iface=iface, code_dt=code_dt, code_cs=code_cs, deactivate_message=deactivate_message)
        layer_manager.setAuthId('9mtq103')
        layer_manager.loadFromExcel("K:/Profils SIG/QGIS/Référence des couches.xlsx")
        return layer_manager

    def __str__ (self): return f"LayerManager ({self.layers.shape[0]} layers)"
    
    def __repr__ (self): return f"LayerManager ({self.layers.shape[0]} layers)"

    def activateMessages(self): self.deactivate_message = False

    def addLayer(self, layer_name, layer_info):
        """ 
        Méthode qui permet d'ajouter une couche à l'index
        
        Args:
            - layer_name (str): Le nom unique de la couche
            - layer_info (Pandas Series): Une series Pandas contenant les informations de la couche
        """
        if layer_name in self.getLayersName(): return self.showMessage(
            "Add Layer",
            f"Le nom {layer_name} est déjà dans l'index des couches",
            Qgis.Critical,
            return_value=False)
        # Ajouter la couche à l'index
        self.layers.loc[layer_name] = layer_info
        return True

    def addLayerToMap(self, task_load_layer, layer_info, use_style=False):
        """
        Méthode qui permet d'ajouter une couche au projet à partir d'un QgsTask.

        Args: 
            - task_load_layer (QgsTask): La tache avec la couche charger 
            - layer_info (dict): Les infos de la couche
            - use_style (bool/str): Le style de la couche a ajouter 
        """
        # Ajouter la couche au projet
        map_layer = QgsProject.instance().addMapLayer(task_load_layer.getLayer())
        # Définir un style si spécifié
        if use_style:
            styles = layer_info[self.c_styles]
            if use_style in styles: map_layer.loadNamedStyle(styles[use_style])
            elif os.path.exists(use_style) and use_style[-4:] == ".qml": map_layer.loadNamedStyle(use_style)
        if self.iface: self.iface.layerTreeView().refreshLayerSymbology(map_layer.id())
        del task_load_layer

    def addLayerRequest(self, layer_name, request_name, request, only_where_clause=False):
        """ Méthode qui permet d'ajouter une requête au dictionnaire des reuquêtes """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Determiner la requete complete à ajouter
        full_request = request
        if only_where_clause: full_request = self.createRequestFromLayer(layer_name, request)
        
        # Ajouter la requête s'il n'est pas déjà dans le dictionnaire
        if request_name not in layer_info[self.c_requests]: layer_info[self.c_requests][request_name] = full_request

        return full_request

    def clean(self):
        """ Méthode qui permet d'éffacer toutes les couches qui sont chargées """
        del self.loaded_layers
        del self.loaded_layers_datasources
        # Dictionnaire des couches qui sont chargées
        self.loaded_layers = {}
        self.loaded_layers_datasources = {}
        
    def createRequestFromLayer(self, layer_name, **kwargs):
        """
        Méthode qui permet de créer une requete pour filter une couche.
        
        Args:
            - layer_name (str): Le nom de la couche dans l'index des couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
        """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        return self.createRequestFromLayerInfo(layer_info, kwargs=kwargs)
    
    def createRequestFromLayerInfo(self, layer_info, **kwargs):
        """
        Méthode qui permet de créer une requete pour filter une couche à partir
        d'un dictionnaire contenant les infos de la couche.
        
        Args:
            - layer_info (dict): Les infos de la couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
        """
        # Where clause 
        where_clause = kwargs["where_clause"] if "where_clause" in kwargs else ""
        # Use DT
        use_dt = kwargs["use_dt"] if "use_dt" in kwargs else True
        # Use CS
        use_cs = kwargs["use_cs"] if "use_cs" in kwargs else False
        # Extent
        extent = kwargs["extent"] if "extent" in kwargs else None
        # Ids
        ids = kwargs["ids"] if "ids" in kwargs else []

        where = []
        # Définir la portion spatial si besoin et que la couche est un WFS
        if extent:
            if layer_info[self.c_prov] == 'wfs': where.append(f"ST_Intersects(ST_GeometryFromText('{extent.asWktPolygon()}'), geometry)")
            if layer_info[self.c_extention] == ".gpkg":
                where.append(
                    f'''fid IN (SELECT id FROM rtree_{layer_info[self.c_source].split("=")[1]}_geom as indexr 
                    WHERE indexr.maxx >= {extent.xMinimum()} AND indexr.minx <= {extent.xMaximum()} AND indexr.maxy >= {extent.yMinimum()} AND indexr.miny <= {extent.yMaximum()}) 
                    AND ST_Intersects(ST_GeometryFromText('{extent.asWktPolygon()}'), geom)''')
        # Définir la portion identifiant
        if ids:
            if len(ids) == 1: ids += ids
            if layer_info[self.c_id_type] == 'str': where.append("%s in ('%s')" % (layer_info[self.c_id_name], "', '".join([str(id) for id in ids])))
            elif layer_info[self.c_id_type] == 'int': where.append("%s in (%s)" % (layer_info[self.c_id_name], ", ".join(ids)))
        
        # Définir la portion DT
        request_dt = None
        if use_dt and not pd.isna(layer_info[self.c_dt]) and not pd.isna(layer_info[self.c_type_dt]):
            # Vérifier si la DT doit être celle par défault
            if isinstance(use_dt, bool) and self.hasDT(): request_dt = self.dt
            # Sinon retrourner la DT selon un code ou un nom
            else: request_dt = self.quebec.getDT(use_dt)
            # Vérifier si une dt est déterminer
            if request_dt:
                # Mettre la valeur du code dans la requete
                if layer_info[self.c_type_dt] == "code": where.append(f"{layer_info[self.c_dt]} LIKE '{request_dt.getCode(as_string=True)}'")
                # Mettre la valeur du nom dans la requete selon le type
                else: where.append(f"{layer_info[self.c_dt]} LIKE '{request_dt.getName(layer_info[self.c_type_dt])}'")
            # Sinon mettre la valeur du use_dt
            elif not isinstance(use_dt, bool): where.append(f"{layer_info[self.c_dt]} LIKE '{str(use_dt)}'")
        
        # Définir la portion CS
        if use_cs and not pd.isna(layer_info[self.c_cs]) and not pd.isna(layer_info[self.c_type_cs]):
            request_cs = None
            # Vérifier si le CS doit être celle par défault
            if isinstance(use_cs, bool) and self.hasCS(): request_cs = self.cs
            # Sinon retrourner le CS selon un code ou un nom
            else:
                # Utiliser la DT si elle est déterminer
                if request_dt: request_cs = request_dt.getCS(use_cs)
                # Sinon regarder dans la province
                else: request_cs = self.quebec.getCS(use_cs)
            # Vérifier si un CS est déterminer
            if request_cs:
                # Mettre la valeur du code dans la requete
                if layer_info[self.c_type_cs] == "code": where.append(f"{layer_info[self.c_cs]} LIKE '{request_cs.getCode(as_string=True)}'")
                # Mettre la valeur du nom dans la requete selon le type
                else: where.append(f"{layer_info[self.c_cs]} LIKE '{request_cs.getName(layer_info[self.c_type_cs])}'")
            # Sinon mettre la valeur du use_cs
            elif not isinstance(use_cs, bool): where.append(f"{layer_info[self.c_cs]} LIKE '{str(use_cs)}'")
            
        # Utiliser une requête
        if where_clause:
            requests = layer_info[self.c_requests]
            if where_clause in requests: where.append(requests[where_clause])
            else: where.append(where_clause)
        if where:
            # Retourner la requete
            if layer_info[self.c_prov] == 'ogr': return ' AND '.join(where)
            if layer_info[self.c_prov] == 'wfs':
                # Determiner le nom de la table dans le serveur WFS
                table_name = literal_eval(layer_info[self.c_source])["typename"]
                if "ms:" in table_name: table_name = table_name[3:]
                # Retourner la requete complète
                return "SELECT * FROM %s WHERE %s" % (table_name, ' AND '.join(where))
        return ''
    
    def deactivateMessages(self): self.deactivate_message = True
    
    def exportToCSV(self, csv):
        """ Methode to export all layers info to a CSV """
        self.layers.to_csv(csv, index=True)
    
    def getColums(self): 
        """ Méthode qui retourn la liste des colums de l'index des couches """
        return self.layers.columns

    def getDataProvider(self, layer):
        if isinstance(layer, str):
            # Aller chercher les informations de la chouche dans le DataFrame
            layer_info = self.getLayerInfo(layer)
            # Retourner rien si le nom n'est pas valide
            if layer_info is None: return layer_info
        else: layer_info = layer
        return layer_info[self.c_prov]

    def getDefaultStyle(self, layer):
        if isinstance(layer, str):
            # Aller chercher les informations de la chouche dans le DataFrame
            layer_info = self.getLayerInfo(layer)
            # Retourner rien si le nom n'est pas valide
            if layer_info is None: return layer_info
        else: layer_info = layer
        if layer_info[self.c_dstyle] in self.getLayerStyles(layer_info): return layer_info[self.c_dstyle]
        else: return None

    def getExtention(self, layer):
        if isinstance(layer, str):
            # Aller chercher les informations de la chouche dans le DataFrame
            layer_info = self.getLayerInfo(layer)
            # Retourner rien si le nom n'est pas valide
            if layer_info is None: return layer_info
        else: layer_info = layer
        return layer_info[self.c_extention]
    
    def getLayer(self, layer_name, load_layer=False, **kwargs):
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
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir la source de la couche
        data_source = self.getLayerDataSource(layer_info, kwargs=kwargs)
        # Retourner la couche à partir du dictionnaire si elle est déjà chargé
        if self.isLayerLoaded(layer_name, data_source): return self.loaded_layers[layer_name]
        # Définir la couche
        layer = QgsVectorLayer(data_source, layer_name, layer_info[self.c_prov])
        if load_layer: 
            self.loaded_layers[layer_name] = layer
            self.loaded_layers_datasources[layer_name] = data_source
        # Retourner la couche 
        return layer
    
    def getLayerTask(self, layer_name, **kwargs):
        """ 
        Méthode qui permet créer une QgsTask pour charger une couche

        Args:
            - layers_names (list): Les noms des couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
            - epsg (int): Code EPSG d'une projection utiliser si disponible
        """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir la source de la couche
        data_source = self.getLayerDataSource(layer_info, kwargs=kwargs)
        # Retourner la couche 
        return LoadLayer(data_source, layer_name, layer_info[self.c_prov])

    def getLayersTask(self, layers_names, **kwargs):
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
        for idx, name in enumerate(layers_names):
            # Aller chercher les informations de la chouche dans le DataFrame
            layer_info = self.getLayerInfo(name)
            # Retourner rien si le nom n'est pas valide
            if layer_info is None: return layer_info
            
            # Where clause 
            if "where_clause" in kwargs and idx < len(kwargs["where_clause"]): where_clause = kwargs["where_clause"][idx]
            else: where_clause = ""
            # Use DT
            if "use_dt" in kwargs and idx < len(kwargs["use_dt"]): use_dt = kwargs["use_dt"][idx]
            else: use_dt = True
            # Use CS
            if "use_cs" in kwargs and idx < len(kwargs["use_cs"]): use_cs = kwargs["use_cs"][idx]
            else: use_cs = False
            # Extent
            if "extent" in kwargs and idx < len(kwargs["extent"]): extent = kwargs["extent"][idx]
            else: extent = None
            # Ids
            if "ids" in kwargs and idx < len(kwargs["ids"]): ids = kwargs["ids"][idx]
            else: ids = []
            # EPSG
            if "epsg" in kwargs and idx < len(kwargs["epsg"]): epsg = kwargs["epsg"][idx]
            else: epsg = None
            
            # Définir la source de la couche
            data_source = self.getLayerDataSource(layer_info, where_clause=where_clause, extent=extent, ids=ids, use_dt=use_dt, use_cs=use_cs, epsg=epsg)
            layers[name] = {"data_source": data_source, "provider": layer_info[self.c_prov]}
        # Retourner la Task 
        return LoadLayers(layers)
    
    def getLayerDataSource(self, layer_info, **kwargs):
        """
        Méthode qui permet de definir la source de la couche à partir
        du dictionnaire contenant les infos de la couche.
        
        Args:
            - layer_name (str): Le nom de la couche dans l'index des couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
            - epsg (int): Code EPSG d'une projection utiliser si disponible
        """
        request = self.createRequestFromLayerInfo(layer_info, kwargs=kwargs)
        # EPSG
        epsg = kwargs["epsg"] if "epsg" in kwargs else None

        provider = layer_info[self.c_prov]
        # Retourner la source de type OGR (geojson, shapefile, geopackage etc.) 
        if provider == "ogr": return self.getLayerDataSourceOGR(layer_info, use_request=request)
        # Retourner la source de type WFS
        elif provider == "wfs": return self.getLayerDataSourceWFS(layer_info, use_request=request, epsg=epsg)
        # Sinon la source de la couche est invalide
        else: return self.showMessage("Invalid DataProvider", f"Le DataProvider {self.c_prov} n'est pas valide", Qgis.Critical)
    
    def getLayerDataSourceOGR(self, layer_info, use_request=None):
        """ Méthode qui permet de definir une source de type OGR à partir des informations dans le DataFrame """
        source = layer_info[self.c_source]
        # Ajouter un filtre si spécifié 
        if use_request: source += "|subset=" + use_request
        return source
        
    def getLayerDataSourceWFS(self, layer_info, use_request=None, epsg=None):
        """ Méthode qui permet de definir une source de type WFS à partir des informations dans le DataFrame """
        source = QgsDataSourceUri()
        # Dictionnaire des parmaètres qui définissent la source
        params = literal_eval(layer_info[self.c_source])
        # Définir le paramètre de l'url
        source.setParam('url', params['url'])
        # Définir le paramètre de l'epsg
        if epsg is None: epsg = params['srsname']
        source.setParam('srsname', epsg)
        # Définir le paramètre de la version
        source.setParam('version', params['version'])
        # Définir le paramètre du nom de la table dans le service web
        source.setParam('typename', params['typename'])
        
        if use_request: source.setSql(use_request)
        
        if self.authid: source.setAuthConfigId(self.authid)
            
        return source.uri(False)
    
    def getLayerField(self, layer_name, field_name):
        """ 
        Méthode qui retourner la valeur d'une information pour la couche
        
        Args: 
            - layer_name (str): Le nom de la couche dans l'index
            - field_name (str): Le nom du champ à retourner l'info
        """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        
        if layer_info[field_name] is np.nan: return None
        else: return layer_info[field_name]

    def getLayerIdField(self, layer_name):
        """ Méthode qui permet de retourner le nom du champs de l'identifiant de la couche"""
        return self.getLayerField(layer_name, self.c_id_name)
        
    def getLayerDTField(self, layer_name):
        """ Méthode qui permet de retourner le nom du champs contenant la DT dans la couche """
        return self.getLayerField(layer_name, self.c_dt)
        
    def getLayerCSField(self, layer_name):
        """ Méthode qui permet de retourner le nom du champs contenant le CS dans la couche """
        return self.getLayerField(layer_name, self.c_cs)
    
    def getLayerInfo(self, layer_name):
        """ Methode pour retourner les informations sur la couche dans le DataFrame """
        # Aller chercher les informations de la couche dans le DataFrame
        if layer_name in self.layers.index: return self.layers.loc[layer_name]
        message_text = f"Le nom {layer_name} n'est pas dans l'index des couches",
        return self.showMessage("Get Layer", message_text, Qgis.Critical)
    
    def getLayerRequests(self, layer_name):
        """ Méthode qui retourn la liste des noms de requête """
        return list(self.getLayerField(layer_name, self.c_requests).keys())
    
    def getLayerSource(self, layer_name):
        """ Méthode qui retourn la sources d'une couche """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        if layer_info[self.c_prov] == "wfs": return literal_eval(layer_info[self.c_source])
        else: return layer_info[self.c_source]
    
    def getLayerStyles(self, layer):
        """ Méthode qui retourn la liste des noms de requête """
        if isinstance(layer, str):
            # Aller chercher les informations de la chouche dans le DataFrame
            layer_info = self.getLayerInfo(layer)
            # Retourner rien si le nom n'est pas valide
            if layer_info is None: return layer_info
        else: layer_info = layer  
        return list(layer_info[self.c_styles].keys())
    
    def getLayersName(self, recherche="", use_tags=True):
        """ 
        Méthode qui permet de retourner les couches dans la gestionnaire de couche 
        selon un text de recherche.
        
        Args:
            - recherche (str): Texte qui permet de rechercher du text dans la liste des couches
            - use_tags (bool): Utiliser les tags de la couche pour la recherche
        """
        layer_names = []
        if recherche:
            for layer_name in self.layers.index:
                list_of_text_search = [layer_name]
                if use_tags: list_of_text_search += self.getTags(layer_name)
                for text in list_of_text_search: 
                    if recherche.lower() == text.lower()[:len(recherche)]:
                        layer_names.append(layer_name)
                        break
                    if len(recherche) > 1 and recherche.lower() in text.lower():
                        layer_names.append(layer_name)
                        break
        else: layer_names = self.layers.index
        return layer_names
        
    def getMapLayers(self, layer_name, use_name=True, use_source=True):
        """
        Méthode qui retourne une liste de QgsMapLayer qui sont dans le projet selon la source et/ou le nom de la couche
        
        Args:
            - layer_name (str): Le nom de la couche dans l'index
            - use_name (bool): Utiliser le nom de la couche comme recherche
            - use_source (bool): Utiliser la source de la couche comme recherche
        """ 
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir la source de la couche
        data_source = self.getLayerDataSource(layer_info)
        layers = []
        # Parcourir les couches de l'instance du projet
        for layer_id in QgsProject.instance().mapLayers():
            # La référence de la couche courant dans la boucle
            layer = QgsProject.instance().mapLayer(layer_id)
            # Sources de la couche courant dans la boucle
            data = layer.dataProvider()
            
            # Vérifier s'il faut vérifier par nom et si le nom des couches sont indentique
            if use_name and layer_name==layer.name(): layers.append(layer)
            # Vérifier s'il faut vérifier par source et si le type de couche sont indentique
            elif use_source and layer_info[self.c_prov] == data.name().lower():
                if layer_info[self.c_prov] == 'ogr':
                    # Retirer la couche du projet si les sources OGR sont indentique
                    if data_source == data.dataSourceUri().split('|')[0]: layers.append(layer)
                elif layer_info[self.c_prov] == 'wfs':
                    # Parametres composant la source de la couche à supprimer
                    params = literal_eval(layer_info[self.c_source])
                    # Parametres composant la source de la couche à comparer
                    uri = data.uri()
                    # Vérifier si le nom de la source WFS et le lien vers le WFS sont indentique 
                    if params['url'] == uri.param("url") and params['typename'] == uri.param("typename"): layers.append(layer)
        return layers
    
    def getRequest(self, source, request, **kwargs):
        """ Méthode qui permet de créer une requete avec le noms ou les informations de la couche"""
        # Créer la requete avec le nom de la couche si la source est un text 
        if isinstance(source, str): return self.getRequestFromLayerName(source, request, kwargs=kwargs)
        # Sinon créer la requete avec les informations
        else: return self.getRequestFromLayerInfo(source, request, kwargs=kwargs)
    
    def getRequestFromLayerInfo(self, layer_info, request, **kwargs):
        """ Méthode qui permet de créer une requete avec les informations de la couche """
        # Dictionnaire des requetes dans les paramètres
        list_requests = layer_info[self.c_requests]
        # Définir la requete
        # Avec la requete enregistrer si la requete demander est un index du dictionnaire
        if request in list_requests: use_request = list_requests[request]
        # Sinon avec la requete en entrée
        else: use_request = request
        # Remplacer des valeurs si des arguments sont spécifié
        for key, value in kwargs.items(): use_request = use_request.replace(f'@{key}@', value)
        # Retourner la requete determiner
        return use_request
    
    def getRequestFromLayerName(self, layer_name, request, **kwargs):
        """ Méthode qui permet de créer une requete avec le nom de la couche """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Retrourner la requete selon la méthode avec les infos 
        return self.getRequestFromLayerInfo(layer_info, request, kwargs=kwargs)
    
    def getTags(self, layer_name):
        """ Méthodes qui permet de retourner la liste des tags de la couche """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # OPTIMISATION: Mettre des listes vides dans l'initialisation des tags lorsque aucun tag est défini
        tags = layer_info[self.c_tag]
        if tags: return tags
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
    
    def isLayerLoaded(self, layer_name, data_source=None):
        """ Méthode qui permet de vérifier si la couche est chargée ou non """
        if layer_name not in self.loaded_layers: return False
        if data_source is None: return True
        return self.loaded_layers_datasources[layer_name] == data_source
    
    def isLayerInProject(self, layer_name, use_name=True, use_source=False):
        """
        Méthode qui permet de vérifier si une couche est dans le projet.
        La recherche peut ce faire par nom de la couche et/ou la source de la cocuhe

        Args:
            - layer_name (str): Nom de la couche dans l'index
            - use_name (bool): Utiliser le nom de la couche comme recherche
            - use_source (bool): Utiliser la source de la couche comme recherche 
        """
        return len(self.getMapLayers(layer_name, use_name=use_name, use_source=use_source)) > 0
    
    def loadData(self, file):
        """
        Méthode qui permet de charger des informations sur des couches à partir d'un
        Excel ou d'un CSV.

        Args:
            - file (str): Le chemin vers le fichier (*.csv ou *.xlsx) à charger
        """
        # Verifier si le chemin vers le fichier est valide
        if not os.path.exists(file): return self.showMessage(
            "Load info",
            f"Le fichier ({file}) n'existe pas",
            Qgis.Critical,
            return_value=False)
        # Vérifier que le fichier a une extention
        if not "." in file: return self.showMessage(
            "Load info",
            f"Le fichier ({file}) doit avoir une extention",
            Qgis.Critical,
            return_value=False)
            
        extention = file.split(".")[1]
        if extention == "csv": layers = pd.read_csv(file, index_col=0)
        elif extention == "xlsx": layers = pd.read_excel(file, index_col=0)
        else: return self.showMessage(
            "Load info",
            f"Le fichier ({file}) doit être un Document .csv ou .xlsx",
            Qgis.Critical,
            return_value=False)
        
        # ---------- Convertir les champs ----------
        layers.fillna('')
        # Convertir le champs des requetes en dictionnaire
        layers[self.c_requests] = layers[self.c_requests].apply(lambda x: literal_eval(x))
        # Convertir le champs des styles en dictionnaire
        layers[self.c_styles] = layers[self.c_styles].apply(lambda x: literal_eval(x))
        # Convertir les tags en liste 
        layers[self.c_tag] = layers[self.c_tag].fillna("")
        layers[self.c_tag] = [val.split(";") for val in list(layers[self.c_tag])]
        # Ajouter un champs avec l'extention de fichier pour les type ogr
        extentions = []
        for layer_name in layers.index:
            if layers.loc[layer_name][self.c_prov] == "ogr": extentions.append(os.path.splitext(layers.loc[layer_name][self.c_source])[1].split("|")[0])
            else: extentions.append("")
        layers[self.c_extention] = extentions
        
        # Garder seulement les couches qui n'existe pas dans le dataframe actuelle
        layers = layers.loc[[layer_name for layer_name in layers.index if not layer_name in self.getLayersName()]]
        
        # Ajouter les nouvelles couches au dataframe
        if self.layers.empty: self.layers = layers
        else: self.layers = pd.concat([self.layers, layers])
        
        return True
    
    def loadFromCSV(self, csv):
        """ Methode to load all layers info in a Pandas DataFrame from CSV"""
        return self.loadData(csv)
        
    def loadFromExcel(self, excel_file):
        """ Methode to load all layers info in a Pandas DataFrame from Excel"""
        return self.loadData(excel_file)
    
    def loadLayer(self, layer_name, **kwargs):
        """
        Méthode qui permet de charger une couche en mémoire.

        Args:
            - layer_name (str): Le nom de la couche dans l'index des couches
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
            - epsg (int): Code EPSG d'une projection utiliser si disponible
        """
        self.getLayer(layer_name, load_layer=True, kwargs=kwargs)
        
    def loadLayers(self, layers_name, extent=None, use_dt=True, use_cs=False, epsg=None):
        """ Méthode qui permet de charger plusieurs couche """
        for name in layers_name: self.loadLayer(name, extent=extent, use_dt=use_dt, use_cs=use_cs, epsg=epsg)
    
    def removeLayer(self, layer_name, use_name=True, use_source=False):
        """ Méthode qui permet de retirer une couche, qui se trouve dans l'index d'un QgsProject """
        for layer in self.getMapLayers(layer_name, use_name=use_name, use_source=use_source):
            QgsProject.instance().removeMapLayer(layer.id())
        
    def setAuthId(self, authid):
        """ Méthode qui permet de définir le authentification id à utiliser"""
        self.authid = authid
    
    def setCS(self, code_cs):
        """ Méthode qui permet de définir un CS par défault """
        self.cs = None
        if self.dt:
            cs = self.dt.getCS(code_cs)
            if cs: 
                self.cs = cs
                self.showMessage(
                    title="Définir CS",
                    message=f"Le CS {cs.getName()} a été défini comme CS par défault",
                    level=Qgis.Success)
            else:
                self.showMessage(
                    title="Définir CS",
                    message=f"Le code de CS '{code_cs}' n'est pas valide",
                    level=Qgis.Critical)
        else:
            self.showMessage(
                    title="Définir CS",
                    message=f"La DT n'est pas spécifié",
                    level=Qgis.Critical)
                
    def setDT(self, code_dt):
        """ Méthode qui permet de définir une DT par défault """
        self.dt = self.quebec.getDT(code_dt)
        if self.dt: 
            self.showMessage(
                title="Définir DT",
                message=f"La DT {self.dt.getName()} a été défini comme DT par défault",
                level=Qgis.Success)
        elif code_dt:
            self.showMessage(
                title="Définir DT",
                message=f"Le code de DT '{code_dt}' n'est pas valide",
                level=Qgis.Critical)
            
    
    def setLayerIdField(self, layer_name, id_field, id_type):
        """ Méthode qui permet d'ajouter un champ d'indenifiant à l'index d'une couche """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir le champ d'indentifiant 
        layer_info[self.c_id_name] = id_field
        # Définir le type du champ d'indentifiant 
        layer_info[self.c_id_type] = id_type
    
    def setLayerSource(self, layer_name, source, provider=None):
        """ Méthode qui permet de modifier la source d'une couche """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Unload layer if it's loaded
        if self.isLayerLoaded(layer_name): self.unloadLayer(layer_name)
        # Set layer source
        layer_info[self.c_source] = source
        # Set layer provider if specified
        if provider: layer_info[self.c_prov] = provider

    def showLayer(self, layer_name, load_layer=False, use_style=None, **kwargs):
        """ 
        Méthode qui permet d'ajouter une couche au projet. La couche est charger dans une QgsTask
        et ensuite est ajouter au projet. Un style peut également être défini.

        Args:
            - layer_name (str): Nom de la couche dans l'index 
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (bool/int): La DT à filtrer True = la DT par défault
            - use_cs (bool/int): Le CS à filtrer True = le CS par défault
            - epsg (int): Code EPSG d'une projection utiliser si disponible
        """
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        task_load_layer = self.getLayerTask(layer_name, kwargs=kwargs)
        # Ajouter la tâche
        task_load_layer.taskCompleted.connect(lambda: self.addLayerToMap(task_load_layer, layer_info, use_style=use_style))
        task_load_layer.taskTerminated.connect(lambda: self.showMessage(
                "Erreur de chargement", f"La couche {layer_name} n'a pas été charagé correctement", Qgis.Critical))
        QgsApplication.taskManager().addTask(task_load_layer)
    
    def showMessage(self, title, message, level, duration=3, return_value=None):
        """ Méthode qui permet d'afficher un message dans le projet QGIS """
        # Notifier l'utilisateur que la couche n'a pas été ajouté 
        if self.iface and not self.deactivate_message: self.iface.messageBar().pushMessage(title, message, level=level, duration=duration)
        return return_value

    def unloadLayer(self, layer_name):
        """ Méthode qui permet de retirer une couche de la mémoire """
        del self.loaded_layers[layer_name]
        del self.loaded_layers_datasources[layer_name]

    def unloadLayers(self, layers_name):
        """ Méthode qui permet de retirer des couches de la mémoire """
        for layer_name in layers_name: self.unloadLayer(layer_name)
        
        

class LoadLayers(QgsTask):
    """ Subclass of QgsTask pour charger la source de plusieur couches """
    def __init__(self, layers):
        super().__init__('Load layers', QgsTask.CanCancel)
        self.layers = layers
        self.result_layers = {}
        self.exception = None

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), "Load layers", Qgis.Info)
        try:
            QgsMessageLog.logMessage(f"Loading layers: {', '.join(list(self.layers.keys()))} loaded!", "Load layers", Qgis.Info)
            total = len(self.layers)
            for i, (layer_name, infos) in enumerate(self.layers.items()):
                self.result_layers[layer_name] = QgsVectorLayer(infos["data_source"], layer_name, infos["provider"])
                self.setProgress((i+1*100)/total)
                QgsMessageLog.logMessage(f"Layer {layer_name} loaded!", "Load layers", Qgis.Info)
                if self.isCanceled(): return False
        # Throw exception
        except Exception as e:
            self.exception = e
            return False
        return True

    def finished(self, result):
        if result: QgsMessageLog.logMessage('"{name}" completed\n'.format(name=self.description()), "Load layers", Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage('"{name}" not successful but without exception (probably the task was manually canceled by the user)'.format(name=self.description()), "Load layers", Qgis.Warning)
            else:
                QgsMessageLog.logMessage('"{name}" Exception: {exception}'.format(name=self.description(),exception=self.exception), "Load layers", Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage('"{name}" was canceled'.format(name=self.description()),"Load layers", Qgis.Info)
        super().cancel()
        
    def getLayers(self):
        return self.result_layers

class LoadLayer(QgsTask):
    """ Subclass of QgsTask pour charger la source de plusieur couches """
    def __init__(self, data_source, layer_name, provider):
        super().__init__('Load layer', QgsTask.CanCancel)
        self.data_source = data_source
        self.layer_name = layer_name
        self.provider = provider
        self.layer = None
        self.exception = None

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), "Load layers", Qgis.Info)
        try:
            if self.isCanceled(): return False
            QgsMessageLog.logMessage(f"Loading layer {self.layer_name}", "Load layers", Qgis.Info)
            self.layer = QgsVectorLayer(self.data_source, self.layer_name, self.provider)
            QgsMessageLog.logMessage(f"Layer {self.layer_name} loaded!", "Load layers", Qgis.Info)
            if self.isCanceled(): return False
        # Throw exception
        except Exception as e:
            self.exception = e
            return False
        return True

    def finished(self, result):
        if result: QgsMessageLog.logMessage('"{name}" completed\n'.format(name=self.description()), "Load layer", Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage('"{name}" not successful but without exception (probably the task was manually canceled by the user)'.format(name=self.description()), "Load layers", Qgis.Warning)
            else:
                QgsMessageLog.logMessage('"{name}" Exception: {exception}'.format(name=self.description(),exception=self.exception), "Load layer", Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage('"{name}" was canceled'.format(name=self.description()),"Load layer", Qgis.Info)
        super().cancel()
        
    def getLayer(self):
        return self.layer


pass