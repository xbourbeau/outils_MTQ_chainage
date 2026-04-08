import os
import requests
import json
import logging
import sys

from qgis.core import QgsJsonUtils, QgsFields, QgsField

class iCherche:

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

        self.default_search_list = ["municipalites", "mrc", "lieux.toponyme.lieux-habites", "routes", "lieux.toponyme.hydro", "adresses"]
        self.default_search_list = ["municipalites","mrc","regadmin","lieux", "bornes-km","routes","adresses","sorties-autoroute", "anciennes-municipalites"]
    
    def documentation(self):
        os.startfile("https://geoegl.msp.gouv.qc.ca/apis/icherche/docs")

    def api_base_url(self):
        return "https://geoegl.msp.gouv.qc.ca/apis/icherche/geocode"
    
    def search(self, text:str, types:list=None, geometry:bool=False):
        """
        Exécute une requête HTTP GET sur l'URL fournie, 
        et retourne les coordonnées associées à l'adresse.
        """
        try:
            if types is None: types = self.default_search_list
            url = f"{self.api_base_url()}?type={requests.utils.quote(','.join(types))}&q={requests.utils.quote(text)}&geometry={geometry}"
            response = requests.get(url)
            # Erreur si status code != 200
            response.raise_for_status()
            data = response.json()
            return [{"index":feat.get("index"), "properties": feat.get("properties", {})} for feat in data.get("features", [])]
        
        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None

    def get_search(self, text:str, types:list=None, geometry:bool=True):
        """
        Exécute une requête HTTP GET sur l'URL fournie, 
        et retourne les coordonnées associées à l'adresse.
        """
        try:
            if types is None: types = self.default_search_list
            url = f"{self.api_base_url()}?type={','.join(types)}&q={requests.utils.quote(text)}&geometry={geometry}"
            response = requests.get(url)
            # Erreur si status code != 200
            response.raise_for_status()
            
            fields = QgsFields()
            fields.append(QgsField("nom", type=10))
            return QgsJsonUtils.stringToFeatureList(json.dumps(response.json()), fields)
        
        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None

    def get_adresse(self, adresse: str, geometry: bool = True):
        """
        Exécute une requête HTTP GET sur l'URL fournie, 
        et retourne les coordonnées associées à l'adresse.
        """
        try:
            url = f"{self.api_base_url()}?type=adresses&q={requests.utils.quote(adresse)}&geometry={geometry}"
            response = requests.get(url)
            # Erreur si status code != 200
            response.raise_for_status()
            data = response.json()
            
            fields = QgsFields()
            fields.append(QgsField("code", type=10))
            fields.append(QgsField("nom", type=10))
            fields.append(QgsField("nbUnite", type=10))

            return QgsJsonUtils.stringToFeatureList(json.dumps(data), fields)
        
        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None
        
    def get_municipalite(self, municipalite: str, geometry: bool = True):
        """
        Exécute une requête HTTP GET sur l'URL fournie, 
        et retourne les coordonnées associées à l'adresse.
        """
        try:
            url = f"{self.api_base_url()}?type=municipalites&q={requests.utils.quote(municipalite)}&geometry={geometry}"
            response = requests.get(url)
            # Erreur si status code != 200
            response.raise_for_status()
            data = response.json()
            
            fields = QgsFields()
            fields.append(QgsField("code", type=10))
            fields.append(QgsField("nom", type=10))
            fields.append(QgsField("mrc", type=10))
            fields.append(QgsField("regAdmin", type=10))

            return QgsJsonUtils.stringToFeatureList(json.dumps(data), fields)
        
        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None