# -*- coding: utf-8 -*-

# Import default librairies
import requests
import json
from typing import Union, List
from osgeo import ogr

# Import QGIS librairies
from qgis.core import (QgsVectorLayer, QgsGeometry, QgsField,
                       QgsVectorLayerUtils, QgsPointXY,
                       QgsCoordinateReferenceSystem)
from PyQt5.QtCore import QVariant

# Import module reference 
from ..packages.requests_negotiate_sspi import HttpNegotiateAuth
from ..functions.reprojections import reprojectGeometry

# Idée de développement si c'est possible
# DEV: Ajouter une option pour de faire des chemins de détour?
# DEV: Prioriser certain tronçons exemple (autoroute)?
# DEV: Créer des zones de desserte?

class TrajetSIGO:
    """ Objet qui permet de calculer un itinéraire à partir de l'API SIGO """
    """ PgRouting v.3.2 """
    """ 
    multiplicateur_clsrte = 
    case 
        when clsrte = 'Autoroute' then 1 
        when clsrte = 'Nationale' then 1 
        when clsrte = 'Collectrice de transit' then 2 
        when clsrte = 'Collectrice municipale' then 2 
        when clsrte = 'Artère' then 2 
        when clsrte = 'Régionale' then 2 
        when clsrte = 'Locale' then 4 
        when clsrte = 'Accès aux ressources' then 4 
        when clsrte = 'Accès aux ressources et aux localités isolées' then 4 
        when clsrte = 'Sans classe' then 500 
        when clsrte = 'Rue piétonne' then 10000 
        when clsrte = 'Liaison maritime' then 10000 
    else 	1 end ;
    """


    def __init__(self,
                 start_point:Union[str, tuple, list, QgsPointXY, QgsGeometry],
                 end_point:Union[str, tuple, list, QgsPointXY, QgsGeometry],
                 stops:List[Union[str, tuple, list, QgsPointXY, QgsGeometry]]=[],
                 obstacles:List[Union[str, tuple, list, QgsPointXY, QgsGeometry]]=[],
                 clsrte:bool=True,
                 codeclasse:bool=False, 
                 min_bbox_multiplier:int=2,
                 max_bbox_multiplier:int=5):
        """
        Initialiser un objet TrajetSIGO pour calculer un itinéraire entre deux points avec des arrêts intermédiaires.

        Args:
            start_point (Union[str, tuple, list, QgsPointXY, QgsGeometry]): Le point de départ en format "Long,Lat"
            end_point (Union[str, tuple, list, QgsPointXY, QgsGeometry]): Le point d'arrivée en format "Long,Lat"
            stops (List[Union[str, tuple, list, QgsPointXY, QgsGeometry]], optional): Liste de point intermédiaire en format "Long,Lat". Defaults to [].
            clsrte (bool, optional): : Utiliser la pondération basée sur la classe routière.. Defaults to True.
            codeclasse (bool, optional): Utiliser la pondération basée sur les classes de camionnage. Defaults to True.
            min_bbox_multiplier (int, optional): Nombre de fois de l'étendue minimum des points d'arrêts afin de sélectionner les segments routiers à utiliser (plus le chiffre est haut, plus c'est possible que l'itinéraire trouvé soit le plus optimal).. Defaults to 2.
            max_bbox_multiplier (int, optional): Nombre de fois de l'étendue maximum des points d'arrêts afin de sélectionner les segments routiers à utiliser (il doit être plus grand que le min_bbox_multiplier).. Defaults to 5.
        """
        # Définir le point de départ de l'itinéraire
        self.set_starting_point(start_point)
        # Définir le point d'arrivée de l'itinéraire
        self.set_end_point(end_point)
        # Définir une liste d'arrêts intermédiaire
        self.set_stops(stops)
        # Définir une d'obstacle
        self.set_obstacles(obstacles)
        
        # Définir les paramètres par défaut
        self.clsrte = clsrte
        self.codeclasse = codeclasse
        self.min_bbox_multiplier = min_bbox_multiplier
        self.max_bbox_multiplier = max_bbox_multiplier

        # Défnir les attribut vide de l'itinéraire non calculé 
        self._is_calculated = False
        self._geom = None
        self._cost = None
        self._time_seconds = None
        self._length = None
        self._server_response = None

    def __repr__(self):
        if self.is_calculated():
            return (f"TrajetSIGO(start_point={self._start_point}, "
                    f"end_point={self._end_point}, "
                    f"stops={self.list_stops}, "
                    f"obstacles={self.list_obstacles}, "
                    f"length={self.length()}, "
                    f"time={self.time(formatted=True)}, "
                    f"cost={self.cost()})")
        else:
            return (f"TrajetSIGO(start_point={self._start_point}, "
                    f"end_point={self._end_point}, "
                    f"stops={self.list_stops}, "
                    f"obstacles={self.list_obstacles}, "
                    "Route not calculated yet)")

    def set_starting_point(self, start_point:Union[str, tuple, list, QgsPointXY, QgsGeometry]):
        self._start_point = self.format_point(start_point)

    def set_end_point(self, end_point:Union[str, tuple, list, QgsPointXY, QgsGeometry]):
        self._end_point = self.format_point(end_point)

    def set_stops(self, stops:List[Union[str, tuple, list, QgsPointXY, QgsGeometry]]):
        self.list_stops = [self.format_point(stop) for stop in stops]

    def set_obstacles(self, obstacles:List[Union[str, tuple, list, QgsPointXY, QgsGeometry]]):
        self.list_obstacles = [self.format_point(obstacle) for obstacle in obstacles]

    def all_points(self): return [self._start_point] + self.list_stops + [self._end_point]

    def format_point(self, point:Union[str, tuple, list, QgsPointXY, QgsGeometry]) -> str:
        """
        Permet de formater un point en chaine de caractères "Long,Lat" nécessaire pour l'API SIGO.
        
        * À noter que les liste et tuple fonctionne seulement dans l'hymisphère nord et avec des longitude négative

        Args:
            point (Union[str, tuple, list, QgsPointXY, QgsGeometry]): le point à formater

        Returns: Le point formaté comme suit: "Long,Lat"
        """
        # Vérifier si le type de point est en texte
        if isinstance(point, str): return point
        # Vérifier si le type de point est en tuple ou liste
        elif (isinstance(point, tuple) or isinstance(point, list)) and len(point) == 2:
            # Assurer que les coordonnées sont des float
            coord = [float(c) for c in point]
            # Renvoyer les coordonnées formatées (min/max) en assumant que c'est dans l'hémisphère nord à l'ouest du méridien central
            return f"{min(coord)},{max(coord)}"
        # Vérifier si le type de point est QgsPointXY et retourner les coordonnées formattées
        elif isinstance(point, QgsPointXY): return f"{point.x()},{point.y()}"
        # Vérifier si le type de point est QgsGeometry et retourner les coordonnées formattées
        elif isinstance(point, QgsGeometry): return f"{point.asPoint().x()},{point.asPoint().y()}"
        
        raise ValueError("Invalid point format. Must be str, tuple, list, QgsPointXY, or QgsGeometry.")

    def is_calculated(self): return self._is_calculated

    def has_obstacle(self): return len(self.list_obstacles) > 0

    def url(self):
        """
        Permet de créer et retourner l'url à utiliser pour calculer l'itinéraire

        Returns (str): Le text qui représente l'url du calcule d'itinéraire
        """
        if self.has_obstacle():
            type_name = "tq_routing_v250804"
            obstacles = f"&coordsobstacle={';'.join(self.list_obstacles)}"
        else: 
            type_name = "pg_routing_iterative_multiple"
            obstacles = ""

        # Créer l'url de la requête avec les paramètres nécessaires
        url = ("https://ws.mapserver.mtq.min.intra/applicatif?"
            "service=WFS&request=GetFeature&version=2.0.0&"
            f"srsname=EPSG:3798&typenames={type_name}&"
            f"outputformat=geojson&coordin={';'.join(self.all_points())}&"
            f"clsrte={self.clsrte}&codeclasse={self.codeclasse}&"
            f"{obstacles}") 
        if type_name == "pg_routing_iterative_multiple": url += f"min_bbox_multiplier={self.min_bbox_multiplier}&max_bbox_multiplier={self.max_bbox_multiplier}"

        return url

    def calculate(self, overwrite=False):
        """
        Permet d'envoyer une requête à l'API SIGO pour calculer l'itinéraire
        entre le point de départ et le point d'arrivée, avec des arrêts intermédiaires.

        Args:
            overwrite (bool, optional): Recalculer l'itinéraire, même si déjà calculer. Defaults to False.

        Returns: True si l'itinéraire a été calculé avec succès, sinon False.
        """
        # Vérifier si l'itinéraire a déjà été calculé
        if self.is_calculated() and not overwrite:
            raise Exception("The route has already been calculated. Use the existing data instead of recalculating.")
        
        # Envoyer la requête à l'API SIGO
        self._server_response = requests.get(self.url(), verify=False, auth=HttpNegotiateAuth(), timeout=200)
        # Recupérer les données GeoJSON de la réponse
        geojson_data = self._server_response.json()

        # Parcourir le feature du GeoJSON pour extraire les informations de l'itinéraire
        for feature in geojson_data['features']:
            # Définir la géométrie
            self._geom = json.dumps(feature['geometry'])
            # Définir l'attribut du cout total
            self._cost = feature['properties']["cout_total"]
            # Définir l'attribut du temps total en seconde
            self._time_seconds = feature['properties']["temps_total_secondes"]
            # Définir l'attribut de la longueur total en mètre
            self._length = feature['properties']["long_total"]
            # Indique que l'itinéraire a été bien calculé et que des résultats sont disponibles
            self._is_calculated = True
            # Sortir de la boucle après avoir trouvé le premier feature
            break
        
        return self.is_calculated()

    def length(self):
        if not self.is_calculated():
            raise ValueError("The route has not been calculated yet.")
        return self._length

    def time(self, formatted=False, round_to:str=None):
        """
        Permet de retourner le temps du trajet brut (en seconde) ou formater.
        Ex, formater:
            - 2h 34min 2sec 
            - 8min 2sec

        Args:
            formatted (bool, optional): Fromater les temps en seconde. Defaults to False.
            round_to (str): Arrondire le temps selon (minute|heure|jour)
        """
        # Vérifier que l'itinéraire est bien calculer
        if not self.is_calculated(): raise ValueError("The route has not been calculated yet.")
        seconds = self._time_seconds
        # Arrondir le temps si demandé
        if round_to:
            if round_to not in ['minute', 'heure', 'jour']: raise ValueError("round_to must be one of: 'minute', 'heure', 'jour'")
            # Arrondir en 
            if round_to == 'minute': seconds = round(seconds / 60) * 60
            elif round_to == 'heure': seconds = round(seconds / 3600) * 3600
            elif round_to == 'jour': seconds = round(seconds / 86400) * 86400
        
        # Formater le temps de secondes en texte lisible
        if formatted:
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            parts = []
            if days > 0: parts.append(f"{int(days)} {'jour' if days == 1 else 'jours'}")
            if hours > 0: parts.append(f"{int(hours)} {'h'}")
            if minutes > 0: parts.append(f"{int(minutes)} {'min'}")
            if seconds > 0: parts.append(f"{int(seconds)} {'sec'}")
            return " ".join(parts)
        
        # Sinon retourner le temps brute
        else: return self._time_seconds

    def cost(self):
        if not self.is_calculated():
            raise ValueError("The route has not been calculated yet.")
        return self._cost    

    def server_response(self): 
        return self._server_response

    def geometry(self, crs:Union[QgsCoordinateReferenceSystem, int, str]=None) -> QgsGeometry:
        """
        Permet de récupérer la géométrie de l'itinéraire calculé en tant que QgsGeometry.
        Par défault la géometrie est en EPSG:3798.

        Args:
            crs ([QgsCoordinateReferenceSystem | int | str], optional): Spécifier un CRS en sortie pour la géometrie

        Returns: QgsGeometry: La géometrie de l'itinéraire dans le CRS spécifié (EPSG:3798 par défault)
        """
        # Assurer que l'itinéraire est calculer
        if not self.is_calculated():
            raise ValueError("The route has not been calculated yet.")
        # Renvoyer la géometrie par défault si aucun CRS spécifié
        if crs is None: geom = self._geom
        # Sinon vérifier le CRS et reprojeter la géométrie si nécessaire
        else:
            # Définir le CRS par défault 
            result_crs = QgsCoordinateReferenceSystem("EPSG:3798")
            # Définir le CRS dans lequel retourner la géometrie
            crs = QgsCoordinateReferenceSystem(crs)
            # Assurer que le CRS est valide
            if not crs.isValid(): raise ValueError("Invalid CRS provided.")
            # Reproject the geometry to the desired CRS
            if crs != result_crs: geom = reprojectGeometry(self._geom, result_crs, crs)
            else: geom = self._geom
        
        # Convertir la géométrie JSON en QgsGeometry
        return QgsGeometry.fromWkt(ogr.CreateGeometryFromJson(geom).ExportToWkt())

    def to_memory_layer(self, layer_name="Itinéraire", layer_crs=3798) -> QgsVectorLayer:
        """
        Permet de créer un QgsVectorLayer en mémoire contenant l'itinéraire calculé.

        Returns: Retourne un QgsVectorLayer contenant l'itinéraire calculé
        """
        # Vérifier d'abord si l'itinéraire a été calculé
        if not self.is_calculated(): raise ValueError("The route has not been calculated yet.")
        # Définir le CRS de la couche
        layer_crs = QgsCoordinateReferenceSystem(layer_crs)
        
        # Créer la couche en mémoire  
        memory_layer = QgsVectorLayer(f"MultiLineString?crs={layer_crs.authid()}", layer_name, "memory")

        # Ajouter les champs à la couche
        memory_layer.dataProvider().addAttributes([
            QgsField("cout_total", QVariant.String),
            QgsField("temps_total_secondes", QVariant.String),
            QgsField("long_total", QVariant.String)])
        memory_layer.updateFields()

        # Définir les attributs du trajet calculé
        attrs = {
            0: self.cost(),
            1: self.time(formatted=True, round_to="minute"),
            2: self.length()}
        # Créer un QgsFeature à ajouter dans la couche
        feat = QgsVectorLayerUtils.createFeature(memory_layer, self.geometry(crs=layer_crs), attrs)
        # Ajouter le QgsFeature du trajet dans la couche
        memory_layer.dataProvider().addFeature(feat)
        
        return  memory_layer