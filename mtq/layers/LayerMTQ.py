# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
from ast import literal_eval
from typing import Union, Dict
from qgis.core import QgsVectorLayer, QgsApplication, QgsProject
from qgis.gui import QgisInterface
from ..param import (
    C_ALIAS, C_DEFAULT_STYLE, C_CS, C_DT, C_ID_NAME, C_ID_TYPE, C_TYPE_DT,
    C_NAME, C_PROV, C_REQUESTS, C_SOURCE, C_STYLES, C_TAG, C_TYPE_CS, C_SEARCH_FIELDS,
    C_DESCRIPTION, C_GEOCATALOGUE)
from ..region.imports import *
from .LoadLayer import LoadLayer

class LayerMTQ:
    """ Définition d'un objet LayerMTQ qui permet de représenter une couche QGIS """

    __slots__ = ("layer_id", "layer_name", "layer_provider", "layer_tags",
                 "key_field_name", "key_field_type", "dt_field_name", "dt_field_type",
                 "cs_field_name", "cs_field_type", "layer_styles", "default_style",
                 "layer_requests", "layer_source", "search_fields", "description", "lien_geocatalogue")

    def __init__(self,
                 id,
                 name:str,
                 source:str,
                 provider:str,
                 key_field_name:str="",
                 key_field_type:str="",
                 dt_field_name:str="",
                 dt_field_type:str="",
                 cs_field_name:str="",
                 cs_field_type:str="",
                 description:str="",
                 search_fields:list[str]=[],
                 default_style:str=None,
                 request:Dict[str, str]={},
                 styles:Dict[str, str]={},
                 tags:list[str]=[],
                 lien_geocatalogue:str=""):
        """ 
        Instancier un objet LayerMTQ

        Args:
            - 
        """
        # Set the layer ID
        self.layer_id = id
        # Set the layer name
        self.setName(name)
        # Set la description de la couche
        self.description = description
        # Set the layer source
        self.setSource(source)
        # Set the layer provider
        self.layer_provider = provider
        # Set the layer Key field
        self.setKeyField(key_field_name, key_field_type)
        # Set the layer DT field
        self.setDTField(dt_field_name, dt_field_type)
        # Set the layer CS field
        self.setCSField(cs_field_name, cs_field_type)
        # Set the layer tags
        self.setTags(tags)
        # Set les champs de recherches
        self.setSearchFields(search_fields)
        # Set the layer styles
        self.setStyles(styles, default_style)
        # Set the layer requests
        self.setRequests(request)
        # Set le lien vers le géocatalogue
        self.lien_geocatalogue = lien_geocatalogue

    @classmethod
    def fromPDSerie(cls, layer_name, layer_info:pd.Series):
        """ Constructeur à partir d'une Serie Pandas """
        # Définir la liste des Tags
        if C_TAG in layer_info.index:
            tags = LayerMTQ.formatField(layer_info[C_TAG], ";")
        else: tags = []

        # Définir la liste des champs de recherche
        if C_SEARCH_FIELDS in layer_info.index:
            search_fields = LayerMTQ.formatField(layer_info[C_SEARCH_FIELDS], ";")
        else: search_fields = []

        return cls(
            id=layer_name,
            name=layer_info[C_ALIAS],
            source=layer_info[C_SOURCE],
            provider=layer_info[C_PROV],
            key_field_name=layer_info[C_ID_NAME],
            key_field_type=layer_info[C_ID_TYPE],
            dt_field_name=layer_info[C_DT],
            dt_field_type=layer_info[C_TYPE_DT],
            cs_field_name=layer_info[C_CS],
            cs_field_type=layer_info[C_TYPE_CS],
            description=layer_info[C_DESCRIPTION] if C_DESCRIPTION in layer_info.index else "",
            search_fields=search_fields,
            default_style=layer_info[C_DEFAULT_STYLE] if C_DEFAULT_STYLE in layer_info.index else "",
            request=literal_eval(layer_info[C_REQUESTS]) if C_REQUESTS in layer_info.index else {},
            styles=literal_eval(layer_info[C_STYLES]) if C_STYLES in layer_info.index else {},
            tags=tags,
            lien_geocatalogue=layer_info[C_GEOCATALOGUE] if C_GEOCATALOGUE in layer_info.index else ""
        )

    def __str__ (self): return f"LayerMTQ ({self.name()})"
    
    def __repr__ (self): return f"LayerMTQ ({self.name()})"
    
    @staticmethod
    def formatField(val, seperator=";"):
        if val is np.nan: return []
        return val.split(seperator)

    def addTag(self, tag:str):
        """ Permet d'ajouter un tag à la listes des tags de la couche """
        self.layer_tags.append(tag)

    def addTags(self, tags:list[str]):
        """ Permet d'ajouter des tags à la listes des tags de la couche """
        tags = [tag for tag in tags if tag]
        self.layer_tags.extend(tags)

    def asVectorLayer(self, **kwargs):
        return QgsVectorLayer(self.dataSource(**kwargs), self.name(), self.dataProvider())

    def createRequest(self, request:str):
        """ Permet de créer un clause WHERE SQL pour filtrer selon une requête du dictionnaire de la couche """
        # Ajouter la requête du dictionnaire des requetes si elle est dedans
        return self.requests().get(request, request)

    def createRequestCS(self, cs:CS):
        """ Permet de créer un clause WHERE SQL pour filtrer selon un objet CS """
        # Vérifier si une DT est spécifié
        if self.cs_field_name == "": return None
        if self.cs_field_type == "code": cs_value = cs.code(as_string=True)
        else: cs_value = cs.name(type=self.cs_field_type)
        # Mettre la valeur du nom dans la requete selon le type
        return f"{self.cs_field_name} LIKE '{cs_value}'"

    def createRequestDT(self, dt:DT):
        """ Permet de créer un clause WHERE SQL pour filtrer selon un objet DT """
        # Vérifier si une DT est spécifié
        if self.dt_field_name == "": return None
        if self.dt_field_type == "code": dt_value = dt.code(as_string=True)
        else: dt_value = dt.name(type=self.dt_field_type)
        # Mettre la valeur du nom dans la requete selon le type
        return f"{self.dt_field_name} LIKE '{dt_value}'"

    def createRequestId(self, list_id:list):
        """ Permet de créer un clause WHERE SQL pour filtrer selon une liste d'identifiant """
        if self.key_field_name == "": return None
        if not list_id: return None

        if self.key_field_type == "str": ids = ','.join([f"'{id}'" for id in list_id])
        else: ids = ','.join([str(id) for id in list_id])
        return f"{self.key_field_name} in ({ids})"
        
    def dataProvider(self):
        """ Permet de retourner le provider de la couche """
        return self.layer_provider

    def dataSource(self, **kwargs):
        """
            - where_clause (str): Une clause WHERE en SQL pour filtrer la couche
            - extent (QgsRectangle): Une étendu pour filtrer la couche 
            - ids (list): Une liste d'indentifiant à afficher
            - use_dt (DT): La DT à filtrer True = la DT par défault
            - use_cs (CS): Le CS à filtrer True = le CS par défault
        """
        
        # Liste des conditions à ajouter pour le datasource
        where = []
        # Vérifier si une condition à été spécifié
        if "where_clause" in kwargs:
            if kwargs["where_clause"]: where.append(self.createRequest(kwargs["where_clause"]))
        # Vérifier si une DT est spécifié
        if kwargs.get("dt", False) and self.dt_field_name != "":
            # Ajouter une requete pour filtrer par DT
            where.append(self.createRequestDT(dt=kwargs["dt"]))
        # Vérifier si une CS est spécifié
        if kwargs.get("cs", False) and self.cs_field_name != "":
            # Ajouter une requete pour filtrer par CS
            where.append(self.createRequestCS(cs=kwargs["cs"]))
        # Vérifier si des ID sont spécifié
        if "ids" in kwargs and self.key_field_name != "":
            # Ajouter une requete pour filtrer par ID
            if kwargs["ids"]: where.append(self.createRequestId(list_id=kwargs["ids"]))
        # Retourner le DataSource de la couche
        if where == []: return self.source()
        else: return "{}|subset={}".format(self.source(), " AND ".join(where)) 

    def defaultStyle(self):
        """ Permet de retourner le nom du style par défault de la couche """
        return self.layer_styles.get(self.default_style, None)
    
    def defaultStyleName(self):
        """ Permet de retourner le nom du style par défault de la couche """
        return self.default_style

    def fileExtention(self):
        """
        Permet de retourner l'extention du fichier.
        Ex: .shp
        """
        file, ext = os.path.splitext(self.source())
        return ext

    def id(self):
        """ Permet de retourner l'identifiant de la couche """
        return self.layer_id

    def getDescription(self):
        """ Permet de retourner la description de la couche si disponible """
        return self.description

    def getFile(self):
        """ Permet de retourner le chemin vers le fichier de la couche """
        return self.source()

    def getKeyField(self): 
        """ Permet de retourner le nom du champs d'id de la couche """
        return self.key_field_name

    def getLoadTask(self, **kwargs):
        return LoadLayer(self.dataSource(**kwargs), self.name(), self.dataProvider())

    def getStyle(self, style=None):
        """
        Permet de retourner un style pour la couche.
        Le style par défault est retourné si aucun style est défini

        Args:
            - style (str): Le nom du style
        """
        try: 
            if os.path.splitext(style)[1] == ".qml": return style
        except: pass
        return self.layer_styles.get(style, self.defaultStyle())

    def lienGeocatalogue(self):
        """ Permet de retourner le lien vers le géocatalogue """
        return self.lien_geocatalogue

    def load(self, **kwargs):
        task_load_layer = self.getLoadTask(**kwargs)
        # Ajouter la tâche
        task_load_layer.taskCompleted.connect(lambda: self.returnLayerFromTask(task_load_layer))
        QgsApplication.taskManager().addTask(task_load_layer)

    def name(self)->str:
        """ Permet de retourner le nom de la couche """
        return self.layer_name

    def hasSameSource(self, source):
        """ Permet de vérifier si la couche à la même source de fichier qu'une source en entrée """
        return self.source() == source
            
    def requests(self):
        """ Permet de retourner le dictionnaire des requêtes """
        return self.layer_requests

    def returnLayerFromTask(self, task:LoadLayer):
        return task.getLayer()

    def setCSField(self, cs_field_name:str, cs_field_type:str):
        """
        Permet de définir le champs de la couche qui sert à définir le CS dans la couche
        Les types de CS (code, court, long et complet)
        
        Args:
            - cs_field_name (str): Le nom du champs identifiant le CS
            - cs_field_type (str): Le type d'identifiant du CS utilisé
        """
        if not isinstance(cs_field_name, str): cs_field_name = ""
        if not isinstance(cs_field_type, str): cs_field_type = ""
        
        self.cs_field_name = cs_field_name
        # Identifier le type de réprensentation du CS dans le champs
        if cs_field_type.lower() == "court": self.cs_field_type = "court"
        elif cs_field_type.lower() == "long": self.cs_field_type = "long"
        elif cs_field_type.lower() == "complet": self.cs_field_type = "complet"
        else: self.cs_field_type = "code"

    def setDTField(self, dt_field_name:str, dt_field_type:str):
        """
        Permet de définir le champs de la couche qui sert à définir la DT dans la couche
        Les types de DT (code, court, long et complet)
        
        Args:
            - dt_field_name (str): Le nom du champs identifiant la DT
            - dt_field_type (str): Le type d'identifiant de la DT utilisé
        """
        if not isinstance(dt_field_name, str): dt_field_name = ""
        if not isinstance(dt_field_type, str): dt_field_type = ""
        
        self.dt_field_name = dt_field_name
        # Identifier le type de réprensentation de la DT dans le champs
        if dt_field_type.lower() == "court": self.dt_field_type = "court"
        elif dt_field_type.lower() == "long": self.dt_field_type = "long"
        elif dt_field_type.lower() == "complet": self.dt_field_type = "complet"
        else: self.dt_field_type = "code"

    def setKeyField(self, key_field_name:str, key_field_type:str):
        """
        Permet de définir le champs de la couche qui sert de champs d'identifiant unique
        Les types de champs sont (int et str)
        
        Args:
            - key_field_name (str): Le nom du champs servant d'indentifiant dans la couche
            - key_field_type (str): Le type de champs servant d'indentifiant dans la couche
        """
        if not isinstance(key_field_name, str): key_field_name = ""
        if not isinstance(key_field_type, str): key_field_type = ""
        
        self.key_field_name = key_field_name
        if key_field_type.lower() == "int": self.key_field_type = "int"
        else: self.key_field_type = "str"

    def setName(self, name:str):
        """ Permet de définir le nom de la couche """
        self.layer_name = name

    def setRequests(self, requests:Dict[str, str]):
        """
        Permet de définir des requêtes pouvant être utilisé sur la couche
        
        Args:
            - requests (dict): Un dictionnaire de requête pour la couche
        """
        # Définir le dictionnaire des styles
        self.layer_requests = requests

    def setSearchFields(self, search_fields:list):
        """ Permet de definir les champs pouvant servire de recherche à la couche """
        self.search_fields = [field for field in search_fields if field]

    def setSource(self, source:str):
        """ Permet de définir la source de la couche """
        if os.path.exists(source): self.layer_source = source
        else: raise ValueError(f"La source {source} pour la couche {self.name()} n'existe pas.")

    def setStyles(self, styles:Dict[str, str], default_style=None):
        """
        Permet de définir des styles pouvant être utilisé sur la couche
        
        Args:
            - styles (dict): Un dictionnaire de style pour la couche
            - default_style (str): Un style à utiliser par défault
        """
        # Définir le dictionnaire des styles
        self.layer_styles = styles
        # Définir le style par défault s'il est dans le dictionnaire
        if default_style in self.layer_styles: self.default_style = default_style
        else:
            # Définir une liste de styles
            keys = list(self.layer_styles.keys())
            # Aucun style par défaut si la liste est vide 
            if keys == []: self.default_style = None
            # Sinon définir le style par défault avec la première valeur
            else: self.default_style = keys[0]

    def setTags(self, tags):
        self.layer_tags = []
        self.addTags(tags)

    def searchFields(self):
        """ Permet de retourner la liste des champs pouvant servir à la recherche """
        return self.search_fields

    def styles(self):
        """ Permet de retourner le dictionnaire des styles """
        return self.layer_styles

    def show(self, iface:QgisInterface=None, use_style=True, **kwargs):
        if not use_style is False: style = self.getStyle(use_style)
        else: style = None

        # Ajouter la couche au projet
        map_layer = QgsProject.instance().addMapLayer(self.asVectorLayer(**kwargs))
        # Définir un style si spécifié
        if style: map_layer.loadNamedStyle(style)
        if iface: iface.layerTreeView().refreshLayerSymbology(map_layer.id())

    def source(self):
        """ Permet de retourner la source de la couche """
        return self.layer_source

    def tags(self):
        """ Permet de retourner la liste des tags de la couche """
        return self.layer_tags
    