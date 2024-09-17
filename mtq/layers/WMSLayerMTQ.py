# -*- coding: utf-8 -*-
from qgis.core import QgsDataSourceUri, QgsRectangle, QgsCoordinateReferenceSystem
from ast import literal_eval
from typing import Union, Dict
from .LayerMTQ import LayerMTQ

class WMSLayerMTQ(LayerMTQ):
    """ Définition d'un objet WMSLayerMTQ qui permet de représenter une couche QGIS """

    __slots__ = LayerMTQ.__slots__

    def __init__(self,
                 id,
                 name:str,
                 source:str,
                 provider:str="wms",
                 description:str="",
                 tags:list[str]=[],
                 lien_geocatalogue:str=""):
        """ 
        Instancier un objet WMSLayerMTQ

        Args:
            - 
        """
        LayerMTQ.__init__(
            self,
            id=id,
            name=name,
            source=source,
            provider=provider,
            description=description,
            tags=tags,
            lien_geocatalogue=lien_geocatalogue)

    def __str__ (self): return f"WMSLayerMTQ {self.name()}"
    
    def __repr__ (self): return f"WMSLayerMTQ {self.name()}"

    def dataSource(self, **kwargs):
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
            ids = self.createRequestId(list_id=kwargs["ids"])
            if ids: where.append(ids)
        if "authid" in kwargs: authid = kwargs["authid"]
        # Vérifier si un étendu est spécifié
        if "extent" in kwargs:
            # Ajouter une requete pour filtrer l'étendue
            if kwargs["extent"]: where.append(self.createRequestExtent(extent=kwargs["extent"]))
        
        # Retourner le DataSource de la couche
        if where == []: return self.source(**kwargs)
        else:
            # Determiner le nom de la table dans le serveur WFS
            table_name = self.typename()
            if "ms:" in table_name: table_name = table_name[3:]
            # Retourner la requete complète
            return self.source(
                use_request="SELECT * FROM {} WHERE {}".format(table_name, ' AND '.join(where)),
                **kwargs)

    def fileExtention(self):
        """
        Permet de retourner l'extention du fichier.
        Toujours None pour le WMS
        """
        return None

    def getFile(self):
        """ Permet de retourner le chemin vers le fichier de la couche """
        return None

    def hasSameSource(self, source:QgsDataSourceUri):
        """ Permet de vérifier si la couche à la même source de fichier qu'une source en entrée """
        # TODO: Add the URL verification also
        return self.typename() == source.param("typename")

    def setSource(self, source:str):
        """ Permet de définir la source de la couche """
        source = literal_eval(source)
        self.layer_url = source["url"]
        self.layer_srsname = source["srsname"]
        self.layer_typename = source["typename"]
        self.layer_version = source["version"]

    def source(self, **kwargs):
        """
        Permet de définir la date source de la couche à partir du module QgsDataSourceUri
        de QGIS. 

        Args:
            - authid (str): L'identifiant d'authentification du service web
        """
        source = QgsDataSourceUri()
        # Définir le paramètre de l'url
        source.setParam('url', self.url())
        # Définir le paramètre de l'epsg
        epsg = kwargs.get("epsg", None)
        if epsg is None: epsg = self.srsname()
        source.setParam('crs', QgsCoordinateReferenceSystem(epsg).authid())
        # Définir L'identifiant d'authentification du service web
        if not kwargs.get("authid", None) is None: source.setAuthConfigId(kwargs["authid"])
        # Retoruner le datasource
        return source.uri(False)