import pandas as pd 
import os
from ast import literal_eval
from qgis.core import QgsDataSourceUri, Qgis, QgsVectorLayer
from .fnt import reprojectLayer
from .region import Province

class LayerManager:

    def __init__(self, iface=None, code_dt=None, code_cs=None, deactivate_message=True):
        # DataFrame (vide) contenant tous les informations des couches
        self.layers = pd.DataFrame()
        # Dictionnaire des couches qui sont chargées
        self.loaded_layers = {}
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
        
        '''
            Colum: 
                name = Nom de la couche (doit être unique)
                source = Le chemin pour se rendre à la couche
                provider = Le type de couche
                key_fields = Le nom du champs qui sert d'identifiant
                key_fields_type = Le type du champs qui sert d'identifiant
                code_dt_field = Le nom du champs qui contient un code (format text) de DT 
                code_cs_field = Le nom du champs qui contient un code (format text) de CS
                requests = Un dictionnaire des requetes de la couche
                styles = Un dictionnaire des styles de la couche
        '''
        self.c_name = "name"
        self.c_source = "source"
        self.c_prov = "provider"
        self.c_id_name = "key_fields"
        self.c_id_type = "key_fields_type"
        self.c_dt = "code_dt_field"
        self.c_cs = "code_cs_field"
        self.c_requests = "requests"
        self.c_styles = "styles"

    def activateMessages(self):
        self.deactivate_message = False

    ''' Méthode qui permet d'ajouter une couche à l'index '''
    def addLayer(self, layer_name, layer_info):
        if layer_name in self.getLayersName(): return self.showMessage(
            "Add Layer",
            f"Le nom {layer_name} est déjà dans l'index des couches",
            Qgis.Critical,
            return_value=False)
        # Ajouter lacouche à l'index
        self.layers = self.layers.append(pd.Series(layer_info, name=layer_name, index=self.getColums()))
        return True

    ''' Méthode qui permet d'ajouter une requête au dictionnaire des reuquêtes '''
    def addLayerRequest(self, layer_name, request_name, request, only_where_clause=False):
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

    ''' Méthode qui permet d'éffacer toutes les couches qui sont chargées '''
    def clean(self):
        del self.loaded_layers
        self.loaded_layers = {}

    ''' Méthode qui permet de créer une requete à partir d'une clause WHERE '''
    def createRequestFromLayer(self, layer_name, where_clause='', extent=None, ids=[], use_dt=True, use_cs=False):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        return self.createRequestFromLayerInfo(layer_info, where_clause=where_clause, extent=extent, ids=ids, use_dt=use_dt, use_cs=use_cs)
    
    ''' Méthode qui permet de créer une requete à partir d'une clause WHERE '''
    def createRequestFromLayerInfo(self, layer_info, where_clause='', extent=None, ids=[], use_dt=True, use_cs=False):
        where = []
        # Définir la portion spatial si besoin et que la couche est un WFS
        if extent and layer_info[self.c_prov] == 'wfs': where.append(f"ST_Intersects( ST_GeometryFromText('{extent.asWktPolygon()}'), geometry)")
        # Définir la portion identifiant
        if ids:
            if len(ids) == 1: ids += ids
            if layer_info[self.c_id_type] == 'str': where.append("%s in ('%s')" % (layer_info[self.c_id_name], "', '".join([str(id) for id in ids])))
            elif layer_info[self.c_id_type] == 'int': where.append("%s in (%s)" % (layer_info[self.c_id_name], ", ".join(ids)))
        
        # Définir la portion DT
        if use_dt and not pd.isna(layer_info[self.c_dt]):
            if isinstance(use_dt, bool) and self.dt: where.append(f"{layer_info[self.c_dt]} LIKE '{self.dt.getCode()}'")
            elif not isinstance(use_dt, bool): where.append(f"{layer_info[self.c_dt]} LIKE '{str(use_dt)}'")
            
        # Définir la portion CS
        if use_cs and not pd.isna(layer_info[self.c_cs]):
            if isinstance(use_cs, bool) and self.cs: where.append(f"{layer_info[self.c_cs]} LIKE '{self.cs.getCode()}'")
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
                # Retourner la requete complète
                return "SELECT * FROM %s WHERE %s" % (table_name, ' AND '.join(where))
        return ''
    
    def deactivateMessages(self):
        self.deactivate_message = True
    
    ''' Methode to export all layers info in a Pandas DataFrame '''
    def exportToCSV(self, csv):
        self.layers.to_csv(csv, index=True)
    
    ''' Méthode qui retourn la liste des colums de l'index des couches '''
    def getColums(self):
        return self.layers.columns

    ''' Méthode qui permet de charger une couche et de retourner le QgsVectorLayer '''
    def getLayer(self, layer_name, use_request=None, epsg=None):
        # Retourner la couche à partir du dictionnaire si elle est déjà chargé
        if self.isLayerLoaded(layer_name): return self.loaded_layers[layer_name]
        # Sinon charger et retourner la couche 
        else: return self.loadLayer(layer_name, use_request=use_request, epsg=epsg)
    
    ''' Méthode qui permet de definir la source de la couche à partir des informations dans le DataFrame '''
    def getLayerDataSource(self, layer_info, where_clause='', extent=None, ids=[], use_dt=True, use_cs=False, epsg=None):
        request = self.createRequestFromLayerInfo(
            layer_info,
            where_clause=where_clause,
            extent=extent,
            ids=ids,
            use_dt=use_dt,
            use_cs=use_cs)
        
        provider = layer_info[self.c_prov]
        # Retourner la source de type OGR (geojson, shapefile, geopackage etc.) 
        if provider == "ogr": return self.getLayerDataSourceOGR(layer_info, use_request=request)
        # Retourner la source de type WFS
        elif provider == "wfs": return self.getLayerDataSourceWFS(layer_info, use_request=request, epsg=epsg)
        # Sinon la source de la couche est invalide
        else: return self.showMessage("Invalid DataProvider", f"Le DataProvider {self.c_prov} n'est pas valide", Qgis.Critical)
    
    ''' Méthode qui permet de definir une source de type OGR à partir des informations dans le DataFrame '''
    def getLayerDataSourceOGR(self, layer_info, use_request=None):
        source = layer_info[self.c_source]
        # Ajouter un filtre si spécifié 
        if use_request: source += "|subset=" + request
        return source
        
    ''' Méthode qui permet de definir une source de type WFS à partir des informations dans le DataFrame '''
    def getLayerDataSourceWFS(self, layer_info, use_request=None, epsg=None):
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
    
    ''' Méthode qui retourn la liste des noms de requête '''
    def getLayerIdField(self, layer_name):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        
        return layer_info[self.c_id_name]
    
    ''' Methode pour retourner les informations sur la couche dans le DataFrame '''
    def getLayerInfo(self, layer_name):
        # Aller chercher les informations de la couche dans le DataFrame
        if layer_name in self.layers.index: return self.layers.loc[layer_name]
        return self.showMessage(
            "Get Layer",
            f"Le nom {layer_name} n'est pas dans l'index des couches",
            Qgis.Critical)
    
    ''' Méthode qui retourn la liste des noms de requête '''
    def getLayerRequests(self, layer_name):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        
        return list(layer_info[self.c_requests].keys())
        
    ''' Méthode qui retourn la liste des noms de requête '''
    def getLayerStyles(self, layer_name):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        
        return list(layer_info[self.c_styles].keys())
    
    ''' Méthode qui retourn la liste des noms de couches à l'index '''
    def getLayersName(self):
        return self.layers.index
        
    ''' Méthode qui retourne une liste de QgsMapLayer qui sont dans le projet selon la source et/ou le nom de la couche ''' 
    def getMapLayers(self, projet_instance, layer_name, use_name=True, use_source=True):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir la source de la couche
        data_source = self.getLayerDataSource(layer_info)
        layers = []
        # Parcourir les couches de l'instance du projet
        for layer_id in projet_instance.mapLayers():
            # La référence de la couche courant dans la boucle
            layer = projet_instance.mapLayer(layer_id)
            # Sources de la couche courant dans la boucle
            data = layer.dataProvider()
            
            # Vérifier s'il faut vérifier par nom et si le nom des couches sont indentique
            if use_name and layer_name==layer.name():
                # Retirer la couche du projet
                layers.append(layer)
                continue
            # Vérifier s'il faut vérifier par source et si le type de couche sont indentique
            if use_source and layer_info[self.c_prov] == data.name().lower():
                if layer_info[self.c_prov] == 'ogr':
                    # Retirer la couche du projet si les sources OGR sont indentique
                    if data_source == data.dataSourceUri().split('|')[0]: layers.append(layer)
                elif layer_info[self.c_prov] == 'wfs':
                    # Parametres composant la source de la couche à supprimer
                    params = literal_eval(layer_info[self.c_source])
                    # Parametres composant la source de la couche à comparer
                    uri = data.uri()
                    # Vérifier si le nom de la source WFS et le lien vers le WFS sont indentique 
                    if params['url'] == uri.param("url") and params['typename'] == uri.param("typename"):
                        layers.append(layer)
                        continue
        return layers
    
    
    ''' Méthode qui permet de créer une requete avec le noms ou les informations de la couche'''
    def getRequest(self, source, request, **kwargs):
        # Créer la requete avec le nom de la couche si la source est un text 
        if isinstance(source, str): return self.getRequestFromLayerName(source, request, **kwargs)
        # Sinon créer la requete avec les informations
        else: return self.getRequestFromLayerInfo(source, request, **kwargs)
    
    ''' Méthode qui permet de créer une requete avec les informations de la couche'''
    def getRequestFromLayerInfo(self, layer_info, request, **kwargs):
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
    
    ''' Méthode qui permet de créer une requete avec le nom de la couche'''
    def getRequestFromLayerName(self, layer_name, request, **kwargs):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Retrourner la requete selon la méthode avec les infos 
        return self.getRequestFromLayerInfo(layer_info, request, **kwargs)
    
    def hasCS(self):
        return self.cs is not None
    
    def hasDT(self):
        return self.dt is not None
    
    ''' Méthode qui permet de vérifier si la couche est chargée ou non '''
    def isLayerLoaded(self, layer_name):
        return layer_name in self.loaded_layers
    
    ''' Methode to load all layers info in a Pandas DataFrame '''
    def loadFromCSV(self, csv):
        # Verifier si le chemin vers le csv est valide
        if not os.path.exists(csv): return self.showMessage(
            "Load info",
            f"Le chemin du csv ({csv}) n'existe pas",
            Qgis.Critical,
            return_value=False)
        # Load CSV
        self.layers = pd.read_csv(csv, index_col=0)
        # ---------- Convertir les champs ----------
        # Convertir le champs des requetes en dictionnaire
        self.layers[self.c_requests] = self.layers[self.c_requests].apply(lambda x: literal_eval(x))
        # Convertir le champs des styles en dictionnaire
        self.layers[self.c_styles] = self.layers[self.c_styles].apply(lambda x: literal_eval(x))
        
        return True
        
    ''' Methode to load all layers info in a Pandas DataFrame '''
    def loadFromExcel(self, excel_file):
        # Verifier si le chemin vers le csv est valide
        if not os.path.exists(excel_file): return self.showMessage(
            "Load info",
            f"Le chemin du csv ({excel_file}) n'existe pas",
            Qgis.Critical,
            return_value=False)
        # Load Excel
        self.layers = pd.read_excel(excel_file, index_col=0)
        self.layers.fillna('')
        # ---------- Convertir les champs ----------
        # Convertir le champs des requetes en dictionnaire
        self.layers[self.c_requests] = self.layers[self.c_requests].apply(lambda x: literal_eval(x))
        # Convertir le champs des styles en dictionnaire
        self.layers[self.c_styles] = self.layers[self.c_styles].apply(lambda x: literal_eval(x))
        
        return True
    
    ''' Méthode qui permet de charger une couche '''
    def loadLayer(self, layer_name, use_request=None, epsg=None):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir la source de la couche
        data_source = self.getLayerDataSource(layer_info, use_request=use_request, epsg=epsg)
        # Charger la couche
        self.loaded_layers[layer_name] = QgsVectorLayer(data_source, layer_name, layer_info[self.c_prov])
        # Retourner la couche
        return self.loaded_layers[layer_name]
    
    ''' Méthode qui permet de retirer une couche, qui se trouve dans l'index d'un QgsProjet '''
    def removeLayer(self, projet_instance, layer_name, use_name=True, use_source=False):
        for layer in self.getMapLayers(projet_instance, layer_name, use_name=use_name, use_source=use_source):
            projet_instance.removeMapLayer(layer_id)
        
    ''' Méthode qui permet de définir le authentification id à utiliser'''
    def setAuthId(self, authid):
        self.authid = authid
    
    ''' Méthode qui permet de définir un CS par défault '''
    def setCS(self, code_cs):
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
                
    ''' Méthode qui permet de définir une DT par défault '''
    def setDT(self, code_dt):
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
            
    
    ''' Méthode qui permet d'ajouter un champ d'indenifiant à l'index d'une couche '''
    def setLayerIdField(self, layer_name, id_field, id_type):
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        # Définir le champ d'indentifiant 
        layer_info[self.c_id_name] = id_field
        # Définir le type du champ d'indentifiant 
        layer_info[self.c_id_type] = id_type
    
    ''' Méthode qui permet de modifier la source d'une couche '''
    def setLayerSource(self, layer_name, source, provider=None):
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

    ''' Méthode qui permet d'ajouter une couche au projet '''
    def showLayer(self, layer_name, where_clause='', extent=None, ids=[], use_dt=True, use_cs=False, use_style=None, epsg=None):
        if not self.iface: return None
        # Aller chercher les informations de la chouche dans le DataFrame
        layer_info = self.getLayerInfo(layer_name)
        # Retourner rien si le nom n'est pas valide
        if layer_info is None: return layer_info
        
        # Définir la source de la couche selon le type
        data_source = self.getLayerDataSource(layer_info, where_clause=where_clause, extent=extent, ids=ids, use_dt=use_dt, use_cs=use_cs, epsg=epsg)
        # Ajouter la couche au projet
        layer = self.iface.addVectorLayer(data_source, layer_name, layer_info[self.c_prov])
        # Définir un style si spécifié
        if use_style:
            styles = layer_info[self.c_styles]
            if use_style in styles: layer.loadNamedStyle(styles[use_style])
            elif os.path.exists(use_style) and use_style[-4:] == ".qml": layer.loadNamedStyle(use_style)
            
        # Retourner la couche ajouter
        return layer
    
    ''' Méthode qui permet d'afficher un message dans le projet QGIS '''
    def showMessage(self, title, message, level, duration=3, return_value=None):
        # Notifier l'utilisateur que la couche n'a pas été ajouté 
        if self.iface and not self.deactivate_message: self.iface.messageBar().pushMessage(title, message, level=level, duration=duration)
        return return_value

    ''' Méthode qui permet de retirer une couche de la mémoire '''
    def unloadLayer(self, layer_name):
        del self.loaded_layers[layer_name]

    ''' Méthode qui permet de retirer des couches de la mémoire '''
    def unloadLayers(self, layers_name):
        for layer_name in layers_name: self.unloadLayer(layer_name)
        
        
pass