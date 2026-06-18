import os
import requests
import json
import logging
import sys

from qgis.core import QgsJsonUtils, QgsFields, QgsField

class terrapi:

    def __init__(self):
        # --- 1. Stop logging from crashing on broken QGIS console ---
        logging.raiseExceptions = False

        # --- 2. Remove all existing handlers that QGIS messed up ---
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # --- 3. Add a safe silent handler ---
        root.addHandler(logging.NullHandler())
        root.setLevel(logging.CRITICAL)

        # --- 4. Extra safety for QGIS broken stderr ---
        if sys.stderr is None: sys.stderr = sys.__stderr__

    def documentation(self):
        os.startfile("https://geoegl.msp.gouv.qc.ca/apis/terrapi/docs")

    def help(self): self.documentation()

    def api_base_url(self):
        return "https://geoegl.msp.gouv.qc.ca/apis/terrapi"
    
    def locate(self, type:str, long:float, lat:float, **kwargs):
        """
        Permet de localiser un types de territoires recherchés avec un point

        Args:
            type (str): Type de territoire recherché. Possible de séparer plusieurs types par une virgule
            long (float): Longitude du point 
            lat (float): Latitude du point 
            q (str): Recherche textuelle dans la propriété 'nom'. La recherche est insensible aux accents et aux majuscules.
            sort (str): Tri les résultats selon une ou plusieurs propriétés. Pour inverser le tri, ajouter - devant le nom de la propriété.
            field (str): Retourne les propriétés optionnelles demandées
            limit (str): Limite le nombre de territoires retournés par type.
            geometry (bool): Indique si la géométrie est retournée
            bbox (bool): Indique si le bbox est retourné
            crs (int): Indique dans quelle projection, les géométries sont retournées
            bufferInput (float): Ajoute un buffer (en mètres) autour de la géométrie passée par le paramètre 'loc'.
            bufferOutput (float): Ajoute un buffer (en mètres) autour des territoires retournés.

        Returns: liste des features en dictionnaire JSON
        """
        try:
            url = f"{self.api_base_url()}/locate?type={type}&loc={long},{lat}"
            
            if "q" in kwargs: url += "&q=" + str(kwargs["q"])
            if "sort" in kwargs: url += "&sort=" + str(kwargs["sort"])
            if "field" in kwargs: url += "&field=" + str(kwargs["field"])
            if "limit" in kwargs: url += "&limit=" + str(kwargs["limit"])
            if "geometry" in kwargs: url += "&geometry=" + str(kwargs["geometry"])
            if "bbox" in kwargs: url += "&bbox=" + str(kwargs["bbox"])
            if "crs" in kwargs: url += "&crs=" + str(kwargs["crs"])
            if "bufferInput" in kwargs: url += "&bufferInput=" + str(kwargs["bufferInput"])
            if "bufferOutput" in kwargs: url += "&bufferOutput=" + str(kwargs["bufferOutput"])
            
            response = requests.get(url)
            # Erreur si status code != 200
            response.raise_for_status()

            return response.json().get("features", [])
        
        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None
        
    def locate_municipalite(self, long:float, lat:float, only_name=True, **kwargs):
        for mun in self.locate("municipalites", long=long, lat=lat, **kwargs):
            if only_name: return mun.get("properties").get("nom")
            else: return mun
        return None
    
    def locate_route(self, long:float, lat:float, distance=10, only_name=True, **kwargs):
        kwargs["bufferInput"] = distance
        for route in self.locate("routes", long=long, lat=lat, **kwargs):
            if only_name: return route.get("properties").get("nom")
            else: return route
        return None
    
    def locate_mrc(self, long:float, lat:float, only_name=True, **kwargs):
        for mrc in self.locate("mrc", long=long, lat=lat, **kwargs):
            if only_name: return mrc.get("properties").get("nom")
            else: return mrc
        return None