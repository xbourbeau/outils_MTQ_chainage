# -*- coding: utf-8 -*-
import os
from qgis.core import QgsRectangle
from typing import Union, Dict
from .LayerMTQ import LayerMTQ

class GeopackageLayerMTQ(LayerMTQ):
    """ Définition d'un objet GeopackageLayerMTQ qui permet de représenter une couche QGIS """

    __slots__ = LayerMTQ.__slots__ + ("geopackage",)

    def __init__(self,
                 id,
                 name:str,
                 source:str,
                 provider:str="ogr",
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
        Instancier un objet GeopackageLayerMTQ

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

    def __str__ (self): return f"GeopackageLayerMTQ {self.name()}"
    
    def __repr__ (self): return f"GeopackageLayerMTQ {self.name()}"

    def createRequestExtent(self, extent:QgsRectangle):
        return f'''fid IN (SELECT id FROM rtree_{self.source().split("=")[1]}_geom as indexr 
            WHERE indexr.maxx >= {extent.xMinimum()} AND indexr.minx <= {extent.xMaximum()} AND indexr.maxy >= {extent.yMinimum()} AND indexr.miny <= {extent.yMaximum()}) 
            AND ST_Intersects(ST_GeometryFromText('{extent.asWktPolygon()}'), geom)'''

    def getFile(self):
        """ Permet de retourner le chemin vers le fichier de la couche """
        return self.source().split("|")[0]

    def hasSameSource(self, source):
        """ Permet de vérifier si la couche à la même source de fichier qu'une source en entrée """
        composantes = source.split("|")
        if len(composantes) <= 1: return False
        return os.path.samefile(composantes[0], self.getFile()) and composantes[1] == self.source().split("|")[1]

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
            if kwargs["ids"]: where.append(self.createRequestId(list_id=kwargs["ids"]))
        # Vérifier si un étendu est spécifié
        if "extent" in kwargs:
            # Ajouter une requete pour filtrer l'étendue
            if kwargs["extent"]: where.append(self.createRequestExtent(extent=kwargs["extent"]))

        # Retourner le DataSource de la couche
        if where == []: return self.source()
        else: return "{}|subset={}".format(self.source(), " AND ".join(where)) 

    def fileExtention(self):
        """
        Permet de retourner l'extention du fichier.
        Toujours .gpkg pour le géopackage 
        """
        return ".gpkg"

    def setSource(self, source:str):
        """ Permet de définir la source de la couche """
        file = source.split("|")[0]
        # Vérifier que le géopackage existe
        if not os.path.exists(file): 
            raise ValueError(f"Le geopackage {file} pour la couche {self.name()} n'existe pas.")
        
        self.layer_source = source
        self.geopackage = file
        
