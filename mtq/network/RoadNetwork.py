from qgis.core import (QgsSpatialIndex, QgsWkbTypes, QgsVectorLayer,
    QgsVectorLayerUtils, QgsGeometry, QgsPointXY, QgsField, QgsProject, QgsFeature)
from PyQt5.QtCore import QVariant
try: import networkx as nx
except: pass

from ..fnt.layer import validateLayer

from ..param import (
    DEFAULT_NOM_COUCHE_ROUTE,
    DEFAULT_KEY_FIELD,
    DEFAULT_DIRECTION_FIELD,
    DEFAULT_SPEED_FIELD,
    DEFAULT_GESTION_FIELD,
    DEFAULT_CAMIONNAGE_FIELD)

class RoadNetwork:
    """
    Objet qui permet de calculer des itinéraires et des chemin de détour à partir
    de la couche d'AQ parcours.
    """

    def __init__(self):
        # Créer un graph vide pour le réseau
        self.graph = None
        # Référence à la couche des routes pour le réseau
        self.roads_layer = None
        # Dictionnaire des entitées utiliser pour le réseau
        self.feature_dict = {}
        # Le chemin vers le style à utiliser pour le résultat
        self.style = "C:/Users/xbourbeau/Desktop/Network/detour.qml"
        # Liste des obstacles du réseau
        self.obstacles = {}
        # Index spatial du réseau routier
        self.road_spatial_index = None
        # Vérifier que les imports sont valide
        self.checkImports()

    @classmethod
    def fromProject(
            cls,
            roads_layer_name:str=DEFAULT_NOM_COUCHE_ROUTE,
            key_field:str=DEFAULT_KEY_FIELD,
            direction_field:str=DEFAULT_DIRECTION_FIELD, 
            speed_field:str=DEFAULT_SPEED_FIELD,
            gestion_field:str=DEFAULT_GESTION_FIELD):
        """
        Permet de générer le réseau à partir de la couche de route dans le projet.

        Args:
            roads_layer_name (str): Le nom de la couche des routes 
            key_field (str, optional): Le champs d'identifiant unique. Defaults to DEFAULT_KEY_FIELD.
            direction_field (str, optional): Le champs qui indique la direction de circulation. Defaults to DEFAULT_DIRECTION_FIELD.
            speed_field (str, optional): Le champs qui indique la vitesse sur le segment. Defaults to DEFAULT_SPEED_FIELD.
            gestion_field (str, optional): Le champs qui indique l'autoritée responsable de la gestion du segment. Defaults to DEFAULT_GESTION_FIELD.
        """
        # Créer l'objet RoadNetwork
        network = cls()
        # Valider la couche de AQ parcours dans le projet
        layer_route = validateLayer(
            roads_layer_name,
            [key_field, direction_field, speed_field, gestion_field],
            geom_type=1)
        # Créer le réseau 
        network.createNetwork(
            layer_route,
            key_field=key_field,
            direction_field=direction_field, 
            speed_field=speed_field,
            gestion_field=gestion_field)
        
        return network

    def clear(self):
        """ Permet de reset le réseau """
        self.graph = None
        self.roads_layer = None
        self.road_spatial_index = None
        self.obstacles = {}

    def clearObstacles(self):
        """ Permet de retirer toutes les obstacles du réseau """
        # Parcourir les segments bloqué par chaque l'obstacle
        return all([self.removeObstacle(route_id) for route_id in self.obstacles.keys()])

    def checkImports(self):
        try:
            import networkx as nx
            self.has_lib = True
        except: self.has_lib = False

        return self.has_lib

    def createNetwork(self,
            roads_layer:QgsVectorLayer,
            key_field:str=DEFAULT_KEY_FIELD,
            direction_field:str=DEFAULT_DIRECTION_FIELD, 
            speed_field:str=DEFAULT_SPEED_FIELD,
            gestion_field:str=DEFAULT_GESTION_FIELD):
        """
        Permet de générer le réseau à partir d'une couche de route.

        Args:
            roads_layer (QgsVectorLayer): La couche des routes 
            key_field (str, optional): Le champs d'identifiant unique. Defaults to DEFAULT_KEY_FIELD.
            direction_field (str, optional): Le champs qui indique la direction de circulation. Defaults to DEFAULT_DIRECTION_FIELD.
            speed_field (str, optional): Le champs qui indique la vitesse sur le segment. Defaults to DEFAULT_SPEED_FIELD.
            gestion_field (str, optional): Le champs qui indique l'autoritée responsable de la gestion du segment. Defaults to DEFAULT_GESTION_FIELD.
        """
        if not self.has_lib: return False

        # Vérifier que la couche est linéaire
        if roads_layer.geometryType() != QgsWkbTypes.LineGeometry: return None
        # Reset le réseau
        self.clear()
        self.graph = nx.MultiDiGraph()
        self.roads_layer = roads_layer
        # Créer l'index spatial des routes du réseau
        self.road_spatial_index = QgsSpatialIndex(self.roads_layer.getFeatures(), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        # Liste des noms de champs de la couche
        fields_name = [field.name() for field in roads_layer.fields()]
        # Vérifier si le champs de la direction est valide
        if not direction_field in fields_name: direction_field = None
        # Vérifier si le champs de la vitesse est valide
        if not speed_field in fields_name: speed_field = None
        # Vérifier si le champs pour définir la gestions est valide
        if not gestion_field in fields_name: gestion_field = None

        # Parcourir toute les entitées de la couche
        for feat in roads_layer.getFeatures():
            feat:QgsFeature
            geom = feat.geometry()
            
            # Définir la valeur de direction
            if direction_field: direction = feat[direction_field]
            else: direction = 0

            # Définir la valeur de vitesse
            if speed_field:
                speed = feat[speed_field]
                # Définir une vitesse de 50km si la vitesse est 0 ou invalide
                if not speed: speed = 50
            # Ignorer la vitesse
            else: speed = None

            # Définir la gestion du segment
            if gestion_field: gestion = feat[gestion_field]
            else: gestion = None

            # Définir la clé unique du segment
            key_val = feat[key_field]

            # Liste des points de la ligne
            points = geom.asPolyline()
            start, end = points[0], points[-1]
            
            # Définir les attributs du segments
            edge_data = {'weight': 1,
                         'speed': speed,
                         'length': geom.length(),
                         'id':feat.id(),
                         'gestion':gestion,
                         'direction':direction,
                         'camionnage':''}
            # Ajouter les segments pour le sense de numérisation 
            if direction in [0, 1]: self.graph.add_edge(start, end, key=key_val, **edge_data)
            # Ajouter les segments pour le sense inverse 
            if direction in [0, 2]: self.graph.add_edge(end, start, key=key_val, **edge_data)

    def hasObstacles(self):
        """ Permet de vérifier si le réseau à des obstacles """
        return self.obstacles != {}

    def nodeWeight(self, node, prev_node, next_node, speed_threshold=50):
        """
        Permet 

        Args:
            node (_type_): _description_
            prev_node (_type_): _description_
            next_node (_type_): _description_
            speed_threshold (int, optional): La vitesse limite utiliser pour limiter l'impact des intersections. Defaults to 50.

        Returns:
            float: Le poid du node selon c'est approche
        """
        incoming_speed = self.graph[prev_node][node].get('speed', 0) if prev_node else 0
        outgoing_speed = self.graph[node][next_node].get('speed', 0) if next_node else 0
        
        connection_count = len(list(self.graph.neighbors(node)))
        multiplier = self.graph.nodes[node].get('weight_multiplier', 1)
        base_weight = connection_count * multiplier
        
        if incoming_speed > speed_threshold and outgoing_speed > speed_threshold and abs(incoming_speed - outgoing_speed) < 10:
            # Reduce weight for high-speed consistent transitions
            return base_weight * 0.5
        else: return base_weight

    def createPathLayer(self, path, attributes={}) -> QgsVectorLayer:
        """
        Permet de créer la couche pour un trajet.

        Args:
            path (_type_): Itinéraire sur le réseau
            attributes (dict): Les attibuts de l'itinéraire

        Returns:
            QgsVectorLayer: La couche linéaire qui contient le trajet résultant
        """
        # Créer une couche vectoriel 
        path_layer = QgsVectorLayer("LineString", "Détour", "memory")
        # Définir le CRS avec la couche de route
        path_layer.setCrs(self.roads_layer.crs())
        # Ajouter les champs d'information de l'intinéraire
        path_layer.dataProvider().addAttributes([
            QgsField("length", QVariant.Double),
            QgsField("time_min", QVariant.Double),
            QgsField("time", QVariant.String)])
        path_layer.updateFields()
        # Créer la géometrie de l'itinéraire à parir du path
        line_geom = QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in path])
        # Ajouter une entitée à la couche
        path_layer.dataProvider().addFeature(
            QgsVectorLayerUtils.createFeature(
                path_layer,
                line_geom,
                attributes))
        # Retourner la couche 
        return path_layer
    
    def getEdgesFromPoint(self, point:QgsPointXY):
        """
        Permet de trouver les segments les plus proche d'un point avec la géometrie.
        Plusieurs segments peuvent être retourner si lorsque le segments est bidirectionnelle

        Args:
            point (QgsPointXY): Le point à utiliser pour trouver les segments

        Returns: Liste des 2 sommets et des données des segments les plus proche
        """
        # Identifiant de la route la plus proche
        feat_id = self.getIdRouteFromPoint(point)
        # Retourner les infromations de segments les plus proche
        return [(u, v, d) for u, v, d in self.graph.edges(data=True) if d.get('id') == feat_id]

    def getIdRouteFromPoint(self, point:QgsPointXY):
        """
        Permet de trouver l'identifiant du segments le plus proche d'un point avec la géometrie

        Args:
            point (QgsPointXY): Le point à utiliser pour trouver le segment

        Returns:
            int: L'identifiant de la route la plus proche du point
        """
        # Identifiant de la route la plus proche
        return self.road_spatial_index.nearestNeighbor(point, 1)[0]

    def getNodeFromPoint(self, point:QgsPointXY):
        """ Permet de retourner le node du réseau le plus proche d'un points """
        # Convertir le point en géometry
        geom_point = QgsGeometry.fromPointXY(point)
        # Trouver le node avec la distance la plus courte du point
        return min(self.graph.nodes(), key=lambda n: QgsGeometry.fromPointXY(QgsPointXY(n[0], n[1])).distance(geom_point))

    def addCamionnage(self, layer_camionnage:QgsVectorLayer, key_field:str=DEFAULT_KEY_FIELD, field_class:str=DEFAULT_CAMIONNAGE_FIELD):
        """
        Permet de remplir l'information du réseau sur les accès pour le camionnage.

        Args:
            layer_camionnage (QgsVectorLayer): La couche de camionnage
            key_field (str, optional): Le nom du champs contenant la clé d'identifiant unique du réseau. Defaults to DEFAULT_KEY_FIELD.
            field_class (str, optional): Le nom du champ qui contient l'information de cammionnage. Defaults to DEFAULT_CAMIONNAGE_FIELD.
        """
        # Créer un index du réseau de camionnage avec l'id comme clé
        dict_camion = {i[key_field]: i[field_class] for i in layer_camionnage.getFeatures()}
        # Parcourir toutes les segments du réseau 
        for u, v, key, data in self.graph.edges(data=True, keys=True):
            # Associer la classification du camionnage au segments
            if key in dict_camion: self.graph[u][v][key]["camionnage"] = dict_camion[key]

    def addPathToMap(self, layer:QgsVectorLayer, use_style:str=None):
        """
        Permet d'ajouter la couche du trajet à la carte avec un style.

        Args:
            layer (QgsVectorLayer): La couche du trajet
            use_style (str): Le style de la couche à appliquer. Défaults to None

        Returns:
            QgsMapLayer: La référence de la couche du trajet ajouter dans la carte
        """
        # Ajouter la couche à la carte
        map_layer = QgsProject.instance().addMapLayer(layer)
        # Définir le styles de la couche
        style = use_style if use_style else self.style
        # Définir le style de la couche s'il est défini
        if style: map_layer.loadNamedStyle(self.style)
        # Retourner la référence de la couche dans la carte
        return map_layer

    def addObstacle(self, obstacle_point:QgsPointXY):
        """
        Permet d'ajouter un obstacles au réseau

        Args:
            obstacle_point (QgsPointXY): Points utilisé comme obstacles
        """
        route_ids = []
        # Parcourir les segments les plus proche du point
        for edge in self.getEdgesFromPoint(obstacle_point):
            # Identifiant de la route réprésenter par le segment
            feat_id = edge[2]["id"]
            # Ajouter le segments au dictionnaire des obstacles
            if feat_id in self.obstacles: self.obstacles[feat_id].append(edge)
            else: self.obstacles[feat_id] = [edge]
            # Retirer le segment du graph du réseau
            self.graph.remove_edge(edge[0], edge[1])
            # Retirer la route à l'index spatial
            try: self.road_spatial_index.deleteFeature(self.roads_layer.getFeature(feat_id))
            except: pass
            route_ids.append(feat_id)
        return route_ids

    def addObstacles(self, obstacle_points:list[QgsPointXY]):
        """
        Permet d'ajouter des obstacles au réseau

        Args:
            obstacle_points (list[QgsPointXY]): Liste de points utilisé comme obstacles
        """
        # Liste des identifiants des segments affecter par les obstacles
        route_ids = []
        # Ajouter les obstacle pour chaque points
        for obstacle_point in obstacle_points: route_ids.extend(self.addObstacle(obstacle_point))
        # Retourner les identifiants affecter par les obstacles
        return route_ids

    def removeObstacle(self, route_id:int):
        """ Permet de retirer un obstacle précis selon un indentifiant de route """
        # Parcourir les segments bloqué par chaque l'obstacle
        if not route_id in self.obstacles: return False
        # Ajouter chaque segments au graph du réseau
        for edge in self.obstacles[route_id]: self.graph.add_edge(edge[0], edge[1], **edge[2])
        # Ajouter le segment à l'index spatial
        self.road_spatial_index.addFeature(self.roads_layer.getFeature(route_id))
        # Retirer la route au dictionnaire des obstacles
        self.obstacles.pop(route_id)
        return True

    def calculateWeight(self, u, v, ds, **kwargs):
        """
        Permet de déterminer comment calculer les poids des segments 

        Args:
            u (_type_): Noeud d'origine
            v (_type_): Noeud destination
            d (_type_): Data des segments entre les noeuds
            gestion (list): Liste des gestions permis d'empruter
            camionnage (list): Liste des classifications de camionnage permis d'empruter

        Returns: Poids du segment à emprunter
        """
        # Liste des poids de segments entre les deux noeuds 
        weights = []
        for d in ds.values():
            # Définir l'effet de le poid de la vitesse
            weight = d['length']
            # Vérifier si la vitesse du réseau à été défini
            if d['speed']:
                # Calculer le poids du segments selon la vitesse et la longueur 
                if d['speed'] > 0: weight = (d['length']/1000)*(1/d['speed'])*60
            # Vérifier si la gestion du segments est défini
            if "gestion" in d and "gestion" in kwargs:
                if kwargs["gestion"] != []:
                    # Ajouter un poid infini si la gestion n'est pas dans la liste de gestion permit
                    if not d['gestion'] in kwargs["gestion"]:  weight += float('inf')
            # Vérifier la classification du camionnage est défini
            if "camionnage" in d and "camionnage" in kwargs:
                if kwargs["camionnage"] != []:
                     # Ajouter un poid infini si la classification du cammionage n'est pas dans la liste
                    if not d['camionnage'] in kwargs["camionnage"]:  weight += 200 #float('inf')
            
            # Ajouter le poids du segment à la list si ça valeur n'est pas infini
            if weight != float('inf'): weights.append(weight)
            # Définir le poid dans les attribut du segment
            d['weight'] = weight
        # Retourner un poid null si la list est vide
        if weights == []: return None
        # Sinon retourner le poid minimum
        else: return min(weights)

    def itineraire(self, start_point, end_point, obstacle_points=[], gestion=[], camionnage=[]):
        """
        Permet de calculer un itinéraire sur le réseau entre un point de début et de fin. 

        Args:
            start_point (_type_): Point de début
            end_point (_type_): Point de fin
            obstacle_points (list, optional): Liste des obstacle à ajouter. Defaults to [].
            gestion (list, optional): Liste des autorité de gestion à utiliser. Defaults to [].
            camionnage (list, optional): Liste des classe de camionnage à utiliser. Defaults to [].

        Returns (QgsVectorLayer): La couche de l'itinéraire 
        """
        # Ajouter les obstacles
        if obstacle_points: self.addObstacles(obstacle_points)
        # Définir le noeud de départ
        start_node = self.getNodeFromPoint(start_point)
        # Définir le noeud de fin
        end_node = self.getNodeFromPoint(end_point)

        # Déterminer le chemin le plus court
        try: path = nx.dijkstra_path(
            self.graph,
            start_node,
            end_node,
            weight=lambda u, v, d: self.calculateWeight(u, v, d, gestion=gestion, camionnage=camionnage))
        except nx.NetworkXNoPath: return None

        # Liste des segments de l'itinéraire
        exact_path = []
        # Valeur de la longueur de l'itinéraire
        total_length = 0
        # Valeur du temps de l'itinéraire
        total_time = 0
        # Parcourir les noueuds de l'itinéraire
        for i in range(len(path) - 1):
            # Définir le noeud de début et fin
            u, v = path[i], path[i+1]
            # Définir les informations sur les attributs des segments
            edges_data = self.graph.get_edge_data(u, v)
            # Trouver le poid minimum des segments
            min_weight = self.calculateWeight(u, v, edges_data, gestion=gestion, camionnage=camionnage)
            # Parcourir les informations sur les attributs des segments
            for e, att in edges_data.items():
                # Garder le segment avec le poid le plus petit
                if att["weight"] == min_weight: edge = edges_data[e]
            
            # Déterminer le feature du segment de route
            feat = self.roads_layer.getFeature(edge["id"])
            # Liste des points du segment de route
            points = feat.geometry().asPolyline()
            # Inverser la liste des points si la directions de la ligne est inverse
            if edge["direction"] == 2: points = list(reversed(points))
            # Définir les index des noeuds
            start_idx, end_idx = points.index(u), points.index(v)
            # Définir les points du segments entre les deux noeuds
            if start_idx < end_idx: segment = points[start_idx:end_idx+1]
            else: segment = list(reversed(points[end_idx:start_idx+1]))
            
            # Ajouter les points du segments au path
            exact_path.extend(segment)
            # Ajouter la longueur du segments
            total_length += edge['length']
            # Ajouter le temps du segments
            total_time += edge['weight']
        
        # Ajouter une tolérence de temps pour démarrer
        total_time += 0.4
        # Formater le temps en minutes
        formater_temps = f"{int(round(total_time, 0))} min"
        # Attribute de la ligne d'itinéraire
        att = {0:total_length, 1:total_time, 2:formater_temps}
        # Retoruner la couche de l'itinéraire
        return self.createPathLayer(exact_path, att)

    def cheminDetour(self, route_id:int, show=True, gestion=[], camionnage=[]):
        """
        Permet de calculer un chemin de détour pour un segment du réseau routier.

        Args:
            route_id (int): L'indentifiant du segement de route pour le détour
            show (bool, optional): Ajouter la couche calculer à la carte. Defaults to True.
            gestion (list of str): Liste des gestions à filtrer

        Returns: Le chemin de détour calculer
        """
        # Définir l'entité de la route à calculer le chemin de détour
        feat = self.roads_layer.getFeature(route_id)
        # Définir la géometrie de la ligne
        line = feat.geometry().asPolyline()
        # Ajouter un obstables temporaire sur le segment de la route 
        route_ids = self.addObstacle(feat.geometry().interpolate(feat.geometry().length()/2).asPoint())
        # Définir un itinéraire entre le point de début et de fin du segment
        layer_detour = self.itineraire(line[-1], line[0], gestion=gestion, camionnage=camionnage)
        # Retirer les obstacle temporaire
        for route_id in route_ids: self.removeObstacle(route_id)
        # Ajouter la couche du détour à la carte si spécifier 
        if show: return self.addPathToMap(layer_detour)
        # Sinon retourner la couche
        else: return layer_detour

    def cheminDetourFromPoint(self, point:QgsPointXY, show=True, gestion=[], camionnage=[]):
        """
        Permet de calculer un chemin de détour pour un point donnée.

        Args:
            point (QgsPointXY): Le point le plus proche du réseau auquel faire un détour
            show (bool, optional): Ajouter la couche calculer à la carte. Defaults to True.
            gestion (list of str): Liste des gestions à filtrer

        Returns: Le chemin de détour calculer
        """
        id_route = self.getIdRouteFromPoint(point)
        return self.cheminDetour(id_route, show=show, gestion=gestion, camionnage=camionnage)


