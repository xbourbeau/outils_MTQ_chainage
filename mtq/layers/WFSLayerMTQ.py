# -*- coding: utf-8 -*-
from qgis.core import QgsDataSourceUri, QgsRectangle, QgsCoordinateReferenceSystem
from ast import literal_eval
from typing import Union, Dict
from .LayerMTQ import LayerMTQ

class WFSLayerMTQ(LayerMTQ):
    """ Définition d'un objet WFSLayerMTQ qui permet de représenter une couche QGIS """

    __slots__ = LayerMTQ.__slots__ + (
        "layer_version", "layer_typename", "layer_srsname", "layer_url")

    def __init__(self,
                 id,
                 name:str,
                 source:str,
                 provider:str="wfs",
                 key_field_name:str="",
                 key_field_type:str="",
                 dt_field_name:str="",
                 dt_field_type:str="",
                 cs_field_name:str="",
                 cs_field_type:str="",
                 description:str="",
                 search_fields:str="",
                 default_style:str=None,
                 request:Dict[str, str]={},
                 styles:Dict[str, str]={},
                 tags:list[str]=[],
                 lien_geocatalogue:str=""):
        """ 
        Instancier un objet WFSLayerMTQ

        Args:
            - 
        """
        LayerMTQ.__init__(
            self,
            id=id,
            name=name,
            source=source,
            provider=provider,
            key_field_name=key_field_name,
            key_field_type=key_field_type,
            dt_field_name=dt_field_name,
            dt_field_type=dt_field_type,
            cs_field_name=cs_field_name,
            cs_field_type=cs_field_type,
            description=description,
            search_fields=search_fields,
            default_style=default_style,
            styles=styles,
            request=request,
            tags=tags,
            lien_geocatalogue=lien_geocatalogue)

    def __str__ (self): return f"WFSLayerMTQ {self.name()}"
    
    def __repr__ (self): return f"WFSLayerMTQ {self.name()}"

    def createRequestExtent(self, extent:QgsRectangle):
        return f"ST_Intersects(ST_GeometryFromText('{extent.asWktPolygon()}'), geometry)"

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
        #if "authid" in kwargs: authid = kwargs["authid"]
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
        Toujours None pour le WFS
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

    def source(self, use_request=None, **kwargs):
        """
        Permet de définir la date source de la couche à partir du module QgsDataSourceUri
        de QGIS. 

        Args:
            - authid (str): L'identifiant d'authentification du service web
            - use_request (str): Définir une requete SQL à utiliser
            - epsg (str): Modifier l'epsg par défault de la couche
        """
        source = QgsDataSourceUri()
        # Définir le paramètre de l'url
        source.setParam('url', self.url())
        # Définir le paramètre maxNumFeatures
        source.setParam('maxNumFeatures', kwargs.get("maxNumFeatures", '1000000'))
        # Définir le paramètre pageSize
        source.setParam('pageSize', kwargs.get("pageSize", '0'))
        # Définir le paramètre pagingEnabled
        source.setParam('pagingEnabled', kwargs.get("pagingEnabled", 'false'))
        # Définir le paramètre de l'epsg
        epsg = kwargs.get("epsg", None)
        if epsg is None: epsg = self.srsname()
        source.setParam('srsname', QgsCoordinateReferenceSystem(epsg).authid())
        # Définir le paramètre de la version
        source.setParam('version', self.version())
        # Définir le paramètre du nom de la table dans le service web
        source.setParam('typename', self.typename())
        # Définir une requête si spécifié
        if use_request: source.setSql(use_request)
        # Définir L'identifiant d'authentification du service web
        if not kwargs.get("authid", None) is None: source.setAuthConfigId(kwargs["authid"])
        # Retoruner le datasource
        return source.uri(False)
        
    def srsname(self):
        return self.layer_srsname

    def typename(self):
        return self.layer_typename

    def url(self):
        return self.layer_url

    def version(self):
        return self.layer_version