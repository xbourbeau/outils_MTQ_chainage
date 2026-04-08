import os
import requests
import json
import logging
import sys
from lxml import etree
from osgeo import ogr

try: from ..packages.requests_negotiate_sspi import HttpNegotiateAuth
except: pass

from ..region.DT import DT, CS

from qgis.core import QgsJsonUtils, QgsFields, QgsField, QgsGeometry

class sigo_applicatif:

    def __init__(self):
        self.session = None
        #https://ws.mapserver.mtq.min.intra/applicatif?q=154001067&service=wfs&request=getfeature&version=2.0.0&typenames=ds&outputformat=json_items&sys=AQR,bgr,cir,dhyd,GEC-SYGEC,gse,gsq,gss,m012,pac,pps,SDE,sem,tre,vhr&limit=5&origin=https://igo.mtq.min.intra

    def is_session_active(self):
        """
        Vérifie si la session est active.
        
        Returns:
            bool: True si la session est active, False sinon.
        """
        return self.session is not None

    def start_session(self):
        """
        Permet de démarrer la session avec les informations d'authentification windows
        """
        try:
            self.session = requests.Session()
            self.session.auth = HttpNegotiateAuth()
            self.session.verify = False
            
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
        
        except Exception as e:
            print(f"Error starting session: {e}")
            self.session = None
        return not self.session is None

    def api_base_url(self):
        return "https://ws.mapserver.mtq.min.intra/applicatif?"
    
    def locate(self, long:float, lat:float):
        if self.is_session_active() == False:
            if not self.start_session(): raise Exception("Impossible de démarrer la session SVN360.")
        
        # Créer l'url de la requête avec les paramètres nécessaires
        url = (f"{self.api_base_url()}"
            "service=WFS&version=1.1.0&request=GetFeature&"
            f"srsname=EPSG:4326&storedquery_id=longlat&"
            f"outputformat=text/xml;%20subtype=gml/3.1.1&"
            f"long={long}&lat={lat}&"
            f"origin=https://igo.mtq.min.intra")

        response = self.session.get(url, timeout=200)
        response.raise_for_status()

        ns = {
            "wfs": "http://www.opengis.net/wfs",
            "gml": "http://www.opengis.net/gml",
            "ms":  "http://mapserver.gis.umn.edu/mapserver" 
        }
        root = etree.fromstring(response.content)
        # Loop over all features
        atts = {}
        for fm in root.findall(".//gml:featureMember", namespaces=ns):
            feature = list(fm)[0]

            # Définir la géometrie
            geom_wrapper = feature.find("ms:geometry", namespaces=ns)
            if geom_wrapper is None or len(geom_wrapper) == 0: continue

            full_tag = feature.tag
            layer_name = full_tag.split("}")[-1]

            nom_region = feature.findtext("ms:nom_unite_admns_court", namespaces=ns)
            if layer_name == "dirct_gen_terrt":
                code = feature.findtext("ms:cod_niv_hierc_2", namespaces=ns)
                atts["DT"] = DT(code, nom_region, self.geometry_from_gml(geom_wrapper), crs=4326)
            elif layer_name == "centr_servc":
                code = feature.findtext("ms:cod_niv_hierc_3", namespaces=ns)
                atts["CS"] = CS(code, nom_region, self.geometry_from_gml(geom_wrapper), crs=4326)

        # Recupérer les données GeoJSON de la réponse
        return atts
    
    def geometry_from_gml(self, geom_wrapper):
        # Get inner GML geometry (<gml:Point>, <gml:Polygon>, etc.)
        gml_geom = etree.tostring(geom_wrapper[0]).decode("utf-8")
        return QgsGeometry.fromWkt(ogr.CreateGeometryFromGML(gml_geom).ExportToWkt())