import requests
import logging
import sys
import webbrowser

try: from ...packages.requests_negotiate_sspi import HttpNegotiateAuth
except: pass

from qgis.core import QgsCoordinateReferenceSystem, QgsPointXY

from ...geomapping.Chainage import Chainage
from ...geomapping.RTSS import RTSS
from ...geomapping.PointRTSS import PointRTSS
from .LocalisationSVN import LocalisationSVN

class SVN360:

    def __init__(self):
        # Initialiser la session avec les informations d'authentification
        self.session = None
        self.images = "file://mtq.min.intra/fic/QC/Depot/Systeme/LidarMobile/Produits/Reseau/ImagesPanoramiques/2023/90/"

        # L'url par défault pour SVN360
        self.default_url = "https://svn360.mtq.min.intra"
        self.default_dev_url = "https://svn360.unit.mtq.min.intra"

        # Définir la liste des epsg géréer par SVN360
        self.list_epsg_possible = ["4326", "3799", "4617"]
        # Définir le rayon de recherche par défaut en mètres
        self.default_rayon = 10

    def start_session(self):
        """
        Permet de démarrer la session avec les informations d'authentification windows pour
        ce connecter à SVN360.
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
            print(f"Error starting SVN360 session: {e}")
            self.session = None
        return not self.session is None
    
    def is_session_active(self):
        """
        Vérifie si la session est active.
        
        Returns:
            bool: True si la session est active, False sinon.
        """
        return self.session is not None

    def create_loc_from_coords(self, x, y, epsg):
        """
        Crée une instance de LocalisationSVN à partir des coordonnées fournies.
        
        Args:
            x (float): Coordonnée X
            y (float): Coordonnée Y
            epsg (int): Code EPSG
        """
        return LocalisationSVN.from_coords(x, y, epsg)
    
    def create_loc_from_point(self, point:QgsPointXY, epsg):
        """
        Crée une instance de LocalisationSVN à partir des coordonnées fournies.
        
        Args:
            point (QgsPointXY): La point contenant les coordonnées X et Y
            epsg (int): Code EPSG
        """
        return LocalisationSVN.from_coords(point.x(), point.y(), epsg)
    
    def create_loc_from_rtss(self, rtss:RTSS, chainage:Chainage):
        """
        Crée une instance de LocalisationSVN à partir du RTSS et du chainage fournis.
        
        Args:
            rtss (RTSS): Code RTSS
            chainage (Chainage): Chainage
        """
        return LocalisationSVN.from_rtss(rtss, chainage)

    def create_loc_from_point_rtss(self, point_rtss:PointRTSS):
        """
        Crée une instance de LocalisationSVN à partir du RTSS et du chainage fournis.
        
        Args:
            point_rtss (PointRTSS):  La point contenant le RTSS et le Chainage
        """
        return LocalisationSVN.from_rtss(point_rtss.getRTSS(), point_rtss.getChainage())

    def open(self, loc:LocalisationSVN=None, rayon=None, ahoriz=None, achamv=None, avert=None):
        """
        Ouvre la localisation dans SVN360 via l'URL.
        
        Args:
            loc (LocalisationSVN): La localisation à ouvrir.
            rayon (float, optional): Le rayon de recherche en mètres. Defaults to None.
            ahoriz (float, optional): Angle horizontal. Defaults to None.
            achamv (float, optional): FOV (zoom). Defaults to None.
            avert (float, optional): Angle de vertical. Defaults to None.
        """
        if loc:
            url = f"{self.default_url}?{loc.url_params()}"
            url += f"&rayon={rayon if rayon is not None else self.default_rayon}"
            if ahoriz is not None: url += f"&ahoriz={ahoriz}"
            if achamv is not None: url += f"&achamv={achamv}"
            if avert is not None: url += f"&avert={avert}"
        else: url = self.default_url
        
        webbrowser.open(url)

    def get_trace_id(self, loc:LocalisationSVN, rayon=None):
        """
        Exécute une requête HTTP GET sur l'URL fournie, 
        et retourne le ideTrace correspondant au plus grand valAnnee.
        """
        if self.is_session_active() == False:
            if not self.start_session(): raise Exception("Impossible de démarrer la session SVN360.")

        rayon = rayon if rayon is not None else self.default_rayon
        try:
            if loc.mode() == "rtss":
                url = f"https://svn360.mtq.min.intra/api/Trace/Rtss/{loc.rtss()}/Chainage/{loc.chainage()}/Rayon/{rayon}"
            else:
                url = f"https://svn360.mtq.min.intra/api/Trace/CoordonneeX/{loc.x()}/CoordonneeY/{loc.y()}/Epsg/{loc.epsg()}/Rayon/{rayon}"
            response = self.session.get(url, timeout=200)
            # Erreur si status code != 200
            response.raise_for_status()
            
            data = response.json()
            traces = data.get("traces", [])
            if not traces: return None
            # Trouver l'élément avec le valAnnee maximum
            latest_trace = max(traces, key=lambda t: t.get("valAnnee", 0))
            return latest_trace.get("ideTrace")

        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None
        
    def get_azimuth_from_trace(self, trace_id, loc:LocalisationSVN, rayon=None):
        """
        Exécute une requête HTTP GET sur l'URL fournie, 
        et retourne le ideTrace correspondant au plus grand valAnnee.
        """
        if self.is_session_active() == False:
            if not self.start_session(): raise Exception("Impossible de démarrer la session SVN360.")

        rayon = rayon if rayon is not None else self.default_rayon
        try:
            if loc.mode() == "rtss":
                url = f"https://svn360.mtq.min.intra/api/PositionGps/Trace/{trace_id}/Rtss/{loc.rtss()}/Chainage/{loc.chainage()}/Rayon/{rayon}"
            else:
                url = f"https://svn360.mtq.min.intra/api/PositionGps/Trace/{trace_id}/CoordonneeX/{loc.x()}/CoordonneeY/{loc.y()}/Epsg/{loc.epsg()}/Rayon/{rayon}"
            response = self.session.get(url, timeout=200)
            # Erreur si status code != 200
            response.raise_for_status()  
            
            data = response.json()
            traces = data.get("positionGps", [])
            if not traces: return None
            # Trouver l'élément avec le valAnnee maximum
            return traces.get("valHeadn", 0)

        except requests.RequestException as e:
            print(f"Erreur lors de l'appel HTTP : {e}")
            return None
        except ValueError as e:
            print(f"Erreur lors du décodage JSON : {e}")
            return None
        
    def get_azimuth(self, loc:LocalisationSVN, rayon=None):
        """
        Permet d'obtenir l'azimut à une localisation donnée.
        
        Args:
            loc (LocalisationSVN): La localisation pour laquelle obtenir l'azimut.
            rayon (float, optional): Le rayon de recherche en mètres. Defaults to None.
        
        Returns:
            float: L'azimut en degrés, ou None si non trouvé.
        """
        trace_id = self.get_trace_id(loc, rayon)
        if trace_id is None: return None

        azimuth = self.get_azimuth_from_trace(trace_id, loc, rayon)
        if azimuth is None: return None
        
        return azimuth