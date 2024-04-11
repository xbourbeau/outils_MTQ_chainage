# -*- coding: utf-8 -*-
# Importer les objects du module core de QGIS 
from qgis.core import (QgsGeometry, QgsPointXY, QgsGeometryUtils, QgsPoint, QgsVectorLayer, QgsField,
                        QgsCoordinateReferenceSystem, QgsSpatialIndex, QgsFeature, QgsWkbTypes)
from qgis.PyQt.QtCore import QVariant
# Importer les fonction de formatage du module
from .format import (verifyFormatRTSS, verifyFormatChainage, verifyFormatPoint,
                    formaterChainage, formaterRTSS)
from .fnt import validateLayer
# Importer la librairie pour des opérations trigo
import math
import numpy as np
from scipy.stats import linregress

# ======================== Nom des options par défault ============================
# Nom de la couche des RTSS 
DEFAULT_NOM_COUCHE_RTSS = 'BGR - RTSS'
# Nom du champ qui contient les RTSS 
DEFAULT_NOM_CHAMP_RTSS = 'num_rts'
# Nom du champ qui contient le chainage de début (None pour vas donnée toute le temps une valeur de 0)
DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE = None
# Nom du champ qui contient le chainage de fin 
DEFAULT_NOM_CHAMP_FIN_CHAINAGE ='val_longr_sous_route'

class featRTSS:
    """
    Class qui défini un objet RTSS.
    Elle permet ainsi de regrouper les méthodes pouvant être associer au RTSS (géocodage)
    """
    __slots__ = ("num_rts", "chainage_f", "geometry", "chainage_d")
    
    def __init__ (self, num_rts, chainage_f, geometry, chainage_d=0):
        """
        Méthode d'initialitation de la class. Le RTSS et chainage de fin peuvent être formater, mais sont stockée
        non formater. Le chainage de début est assumé comme étant 0
        
        Args:
            - num_rts (str): Le numéro de RTSS
            - chainage_f (real/str): Le chainage de fin du RTSS, sois sa longueur en chainage
            - geometry (QgsGeometry): La geometrie du RTSS
            - chainage_d (real/str): Le chainage de début du RTSS, par défault toujours 0
        """
        # Initialiser les informations du RTSS
        self.num_rts = verifyFormatRTSS(num_rts)
        self.chainage_f = verifyFormatChainage(chainage_f)
        self.geometry = geometry
        self.chainage_d = verifyFormatChainage(chainage_d)
        if self.chainage_d is None: self.chainage_d = 0
        
    @classmethod
    def fromFeature(cls, feat, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE):
        """
        Méthode d'initialitation de la class à partir d'une entitée.

        Args:
            - feat (QgsFeature): L'entitié du RTSS
            - nom_champ_rtss (str): Le nom du champ contenant le RTSS
            - nom_champ_long (str): Le nom du champ contenant le chainage de fin
            - chainage_d (str): Le nom du champ contenant le chainage de début
        """
        if isinstance(feat, QgsFeature):
            if chainage_d is None: chainage_d = 0
            else: chainage_d = feat[chainage_d]
            return cls(feat[nom_champ_rtss], feat[nom_champ_long], feat.geometry(), chainage_d=chainage_d)
        else: return cls(None, None, None)
    
    def __str__ (self): return f"{self.num_rts} ({self.chainage_d}, {self.chainage_f})"
    
    def __repr__ (self): return f"featRTSS {self.num_rts} ({self.chainage_d}, {self.chainage_f})"
    
    def getRTSS(self, formater=False):
        """ 
        Méthode qui renvoie le numéro du RTSS.
        
        Args:
            - formater (bool): retourner le RTSS formater
        """
        if formater: return formaterRTSS(self.num_rts)
        else: return self.num_rts
    
    def getRoute(self, as_int=False):
        """ 
        Méthode qui renvoie le numéro de la route
        Ex: 00116-01-120-000C => 00116
        
        Args:
            - as_int (bool): retourner le numéro sous forme de chiffre
        """
        if as_int: return int(self.num_rts[:5])
        else: return self.num_rts[:5]
    
    def getTroncon(self, as_int=False):
        """ 
        Méthode qui renvoie le numéro de troncon du RTSS
        Ex: 00116-01-120-000C => 01

        Args:
            - as_int (bool): retourner le numéro sous forme de chiffre
        """
        if as_int: return int(self.num_rts[5:7])
        else: return self.num_rts[5:7]
        
    def getSection(self, as_int=False):
        """ 
        Méthode qui renvoie le numéro de section du RTSS
        Ex: 00116-01-120-000C => 120
        
        Args:
            - as_int (bool): retourner le numéro sous forme de chiffre
        """
        if as_int: return int(self.num_rts[7:10])
        else: return self.num_rts[7:10]
        
    def getSousSection(self):
        """ 
        Méthode qui renvoie la sous-section du RTSS
        Ex: 00116-01-120-000C => 000C
        """
        return self.num_rts[10:]
    
    def getGeometry(self):
        """ Méthode qui renvoie la géometrie du RTSS """
        return self.geometry
    
    def getChainageFin(self, formater=False):
        """ 
        Méthode qui renvoie le chainage de fin du RTSS, sois sa longueur en chainage.
        
        Args:
            - formater (bool): retourner le chainage formater
        """
        if formater: return formaterChainage(self.chainage_f)
        else: return self.chainage_f
        
    def getChainageDebut(self, formater=False):
        """ 
        Méthode qui renvoie le chainage de début du RTSS.
        
        Args:
            - formater (bool): retourner le chainage formater
        """
        if formater: return formaterChainage(self.chainage_d)
        else: return self.chainage_d
        
    def getChainageOnRTSS (self, chainage):
        """ 
        Méthode qui renvoie le chainage en entrée sur RTSS. 
        Elle s'asure que le chainage ne sois pas plus petit ou plus grand que les chainages du RTSS
        """
        if chainage < self.chainage_d: return self.chainage_d
        elif chainage > self.chainage_f: return self.chainage_f
        else: return chainage
    
    def getDistanceFromPoint(self, point):
        """
        Méthode qui permet de calculer une distance trace d'un point par rapport au RTSS.
        La distance du point par rapport au RTSS (positif = droite / négatif = gauche)
        
        Args:
            - point (QgsPointXY): Le point à trouver la distance du RTSS
        
        Return:
            - dist (float): La distance du point par rapport au RTSS (positif = droite / négatif = gauche)
        """
        # Trouver les vertex du RTSS à proximité du point (avant, plus proche et après)
        id, vertex_id, previous_vertex_id, nextVertexIndex, sqr_dist = self.geometry.closestVertex(point)
        # Verifier si le vertex avant existe donc que le point n'est pas au début complétement de la ligne
        if previous_vertex_id == -1:
            # Trouver le côté (vertex proche => vertex après)
            side = QgsGeometryUtils.segmentSide(self.geometry.vertexAt(vertex_id),
                                                self.geometry.vertexAt(nextVertexIndex),
                                                QgsPoint(point.x(),point.y()))
        else:
            # Trouver le côté ligne(vertex avant => vertex proche)
            side = QgsGeometryUtils.segmentSide(self.geometry.vertexAt(previous_vertex_id),
                                                self.geometry.vertexAt(vertex_id),
                                                QgsPoint(point.x(),point.y()))
        # Retourner la distance et appliquer le coté (1=droit ; -1=gauche)
        return self.geometry.distance(verifyFormatPoint(point)) * side
        
    def getChainageFromPoint(self, point, formater=False):
        """ 
        Méthode qui permet d'associer un chainage le long du RTSS à partir d'un point. Le point peut être sur la 
        la ligne ou avoir un offset. 
        
        Args:
            - point (QgsGeometry/QgsPointXY): Le point à associer un chainage
            - formater (bool): Formater le résultat du chainage
        
        Return:
            - chainage(real/str): Le chainage sur le RTSS le plus proche du point. 
        """
        # Longueur le long de la ligne jusqu'au point le plus proche du point spécifié
        long = self.geometry.lineLocatePoint(verifyFormatPoint(point))
        # Chainage corriger correspondant à la longueur trouvé
        chainage = self.getChainageFromLong(long)
        # Formater si c'est spécifié
        if formater: chainage = formaterChainage(chainage)
        # Retourner le chainage
        return chainage
    
    def getPoint(self, point):
        return self.getPointFromChainage(point.getChainage(), point.getOffset())
        
    def getPointFromChainage(self, chainage, offset=0):
        """
        Méthode qui permet de géocoder un point avec un chainage et un offset sur le RTSS.
        Le offset de la ligne par rapport au RTSS peut être positif pour un offset à droite dans le sense
        de numérisation de la ligne ou négatif pour être à gauche.
        
        Args:
            - chainage (real/str): Le chainage du point à géocoder. Peut être formater ex: (2+252 ou 2252)
            - offset (real): Le offset du point par rapport au RTSS (positif = droite / négatif = gauche)
        """
        chainage = verifyFormatChainage(chainage)
        # Longeur géometrique le long du RTSS correspondant au chainage
        long = self.getLongFromChainage(chainage)
        # Geometry du point à la distance
        geom_point = self.geometry.interpolate(long)
        # Calculer le point avec la distance d'offset
        if offset != 0:
            point = geom_point.asPoint()
            # Angle en radian du RTSS au chainage dans le sense horraire par raport au Nord
            angle = self.geometry.interpolateAngle(long)
            
            """ Les delta X et delta Y sont de base calculer pour le cadrant Nord-Est avec l'angle du RTSS.
            Cependant, les delta reste les mêmes sauf pour le signe peut importe le cadrant
            si l'angle est (90, 180 ou 270) de plus. Le offset représente l'angle de la ligne + 90.
            Donc on applique les deltas pour le cadrant Sud-Est. """

            # Coordonnée offset = coordonnée +/- delta
            x = point.x() + (math.cos(angle) * offset)
            y = point.y() - (math.sin(angle) * offset)
            geom_point = QgsGeometry().fromPointXY(QgsPointXY(x, y))
        # Retourner la géometrie ponctuelle
        return geom_point
    
    def getLine(self, list_points, iterpolate_middle=True, reverse_geom=False):
        line = []
        for idx, point in enumerate(list_points):
            if idx == len(list_points) - 1 or not iterpolate_middle:
                line.append(self.getPoint(point).asPoint())
            else:
                next_point = list_points[idx+1]
                add_line = self.getLineFromChainage(
                    point.getChainage(), next_point.getChainage(),
                    point.getOffset(), next_point.getOffset(),
                    iterpolate_middle=iterpolate_middle, reverse_geom=reverse_geom).asPolyline()
                line += add_line[:-1]
        # Créer la géometrie de la ligne à partir de la liste des vertex
        line_geom = QgsGeometry().fromPolylineXY(line)
        # Retirer des vertex qui serait doublé
        line_geom.removeDuplicateNodes()
        return line_geom
    
    def getLineFromChainage(self, chainage_d, chainage_f, offset_d=0, offset_f=None, iterpolate_middle=True, reverse_geom=False):
        """
        Méthode qui permet de géocoder une ligne à partir d'un chainage de début et de fin.
        La ligne peut être parralel ou non et avoir un offset avec le RTSS. Si seulement un offset est définie ou
        que les deux offset sont pareil, la ligne vas être parallel au RTSS. Si deux offset sont défini,
        La difference entre les deux offset vas être répartie sur la longeur de la ligne. 
        De plus, si les deux chainage sont identique, la ligne va être perpendiculaire au RTSS.
        La ligne peut-être géocoder dans le sense contraire du chainage.
        
        Args:
            - chainage_d (real/str): Le chainage de début. Peut être formater ex: (2+252 ou 2252)
            - chainage_f (real/str): Le chainage de fin. Peut être formater ex: (2+252 ou 2252)
            - offset_d (real): Le offset de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f (real): Le offset de fin de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - iterpolate_middle (bool): L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
            - reverse_geom (bool): L'indicateur pour avoir une line dont la géomtrie est inverse au sense du chainage 
        Return:
            - line_geom (QgsGeometry): La géometrie linéaire géocoder
        """
        # Assurer que les chainage soint en format numérique
        chainage_d = verifyFormatChainage(chainage_d)
        chainage_f = verifyFormatChainage(chainage_f)
        # Donner le même offset de fin si la variable en entrée n'est pas défini
        if offset_f is None: offset_f = offset_d
        is_parallel = (offset_d == offset_f)
        # Inverser les valeurs si les chainage sont inverser
        if chainage_d > chainage_f: 
            chainage_d, chainage_f = chainage_f, chainage_d
            offset_d, offset_f = offset_f, offset_d
            
        # Différence du offset
        offset_diff = offset_f - offset_d
        # Longueur de la nouvelle ligne
        longueur_ligne = chainage_f - chainage_d
        # List des points de la nouvelle ligne
        new_line_vertices = []
        
        # Vérifier que le chainage de début ne dépasse pas le chainage de fin 
        if chainage_d != chainage_f:
            # Calculer le premier point de la ligne (chainage début)
            point = self.getPointFromChainage(chainage_d, offset_d).asPoint()
            # Ajouter le premier point à la ligne
            new_line_vertices.append(point)
            # Vérifier l'indicateur pour faire l'interpolation
            if iterpolate_middle:
                # Parcourir les vertex qui compose le RTSS
                for vertice in self.geometry.vertices():
                    # Chainage le plus proche du vertex
                    current_chainage = self.getChainageFromPoint(QgsPointXY(vertice.x(),vertice.y()))
                    # Arreter l'itération si le vertex dépasse le chainage de fin de la ligne
                    if current_chainage >= chainage_f: break
                    # Vérifier si le vertex se trouve entre les chainages spécifié (début/fin)
                    elif current_chainage > chainage_d:
                        # Prendre le offset de début si la ligne est parallel
                        if is_parallel: current_offset = offset_d
                        # Sinon calculer le offset selon la distance et la difference entre les deux offsets 
                        else: current_offset = (((current_chainage-chainage_d) * offset_diff)/longueur_ligne) + offset_d
                        current_point = self.getPointFromChainage(current_chainage, current_offset).asPoint()
                        # Ajouter le point offset à la ligne
                        new_line_vertices.append(current_point)
            
            # Calculer le dernier point de la ligne (chainage fin)
            point = self.getPointFromChainage(chainage_f, offset_f).asPoint()
            # Ajouter le premier point à la ligne
            new_line_vertices.append(point)
        
        # Vérifier si la ligne est perpendiculaire
        elif offset_f is not None and offset_d != offset_f:
            # Géometry du point au offset de début du RTSS
            geom_point_d = self.getPointFromChainage(chainage_d, offset_d)
            # Géometry du point au offset de fin du RTSS
            geom_point_f = self.getPointFromChainage(chainage_f, offset_f)
            # Ajouter les points à la ligne
            new_line_vertices = [geom_point_d.asPoint(), geom_point_f.asPoint()]
        # Inverser la géometrie
        if reverse_geom: new_line_vertices.reverse()
        # Créer la géometrie de la ligne à partir de la liste des vertex
        line_geom = QgsGeometry().fromPolylineXY(new_line_vertices)
        # Retirer des vertex qui serait doublé
        line_geom.removeDuplicateNodes()
        # Retourner la géometrie de la ligne
        return line_geom
    
    def getPolygon(self, list_points, iterpolate_middle=True):
        list_polygon_points = []
        for idx, point in enumerate(list_points):
            if idx == len(list_points) - 1 or not iterpolate_middle: 
                list_polygon_points.append(self.getPointFromChainage(point.getChainage(), point.getOffset()).asPoint())
            else:
                next_point = list_points[idx+1]
                reverse_geom = point.getChainage() > next_point.getChainage()
                ligne = self.getLineFromChainage(
                    point.getChainage(), next_point.getChainage(),
                    point.getOffset(), next_point.getOffset(),
                    iterpolate_middle=iterpolate_middle, reverse_geom=reverse_geom).asPolyline()
                list_polygon_points += ligne[:-1]
        list_polygon_points.append(list_polygon_points[0])
        # Retourn la géometrie polygonal (Si moins de 3 point la géometrie est NULL)
        return QgsGeometry().fromPolygonXY([list_polygon_points])
    
    def getPolygonFromChainage(self, chainage_d1, chainage_f1, offset_d1, offset_d2, chainage_d2=None, chainage_f2=None, offset_f1=None, offset_f2=None, iterpolate_middle=True):
        """
        Méthode qui permet de géocoder un polygone à partir de quatre combinaisons de chainage/offset
        Le polygone est construit avec deux lignes géocoder. Donc les deux premières combinaisons représente
        une premières ligne géocodé et les deux autre combinaisons représente la deuxième ligne géocoder dans l'autre dirrection.
        
        Args:
            - chainage_d1 (real/str): Le chainage de début de la première ligne. Peut être formater ex: (2+252 ou 2252)
            - chainage_f1 (real/str): Le chainage de fin de la première ligne. Peut être formater ex: (2+252 ou 2252)
            - offset_d1 (real): Le offset de la première ligne de début par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f1 (real): Le offset de la première ligne de fin par rapport au RTSS (positif = droite / négatif = gauche)
            - chainage_d2 (real/str): Le chainage de début de la deuxième ligne. Peut être formater ex: (2+252 ou 2252)
            - chainage_f2 (real/str): Le chainage de fin de la deuxième ligne. Peut être formater ex: (2+252 ou 2252)
            - offset_d2 (real): Le offset de la deuxième ligne de début par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f2 (real): Le offset de la deuxième ligne de fin par rapport au RTSS (positif = droite / négatif = gauche)
            - iterpolate_middle (bool) = L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
        Return:
            - geom (QgsGeometry): La géometrie polygonal géocoder
        """
        pts = [self.setPointRTSS(chainage_d1, offset_d1), self.setPointRTSS(chainage_f1, offset_f1), self.setPointRTSS(chainage_d2, offset_d2), self.setPointRTSS(chainage_f2, offset_f2)]
        # Liste des points composant le polygone
        list_points = [point for point in pts if point]
        return self.getPolygon(list_points, iterpolate_middle=iterpolate_middle)
    
    def getLongFromChainage (self, chainage):
        """ 
        Méthode qui retourne le chainage correspondant à la longueur demandé le long du RTSS
        Chaînage --> Distance géometrique
        
        Args:
            - chainage (float/int): Le chainage à convertir en longueur géometrique 
        
        Return:
            - long_corriger (float/int): La longueur géometrique correspondant au chainage en entrée
    """
        # Longueur du RTSS
        long_rtss = self.geometry.length()
        # Chainage 
        chainage = verifyFormatChainage(chainage)
        # Retourner la longueur geometrique max si le chainage est plus grande que le chainage de fin 
        if chainage >= self.chainage_f: return long_rtss
        # Retourner le chainage de début du RTSS si le chainage est plus petit que le chainage de début du RTSS
        elif chainage <= self.chainage_d: return self.chainage_d
        # Sinon corriger le chainage pour obtenir la longueur géometrique
        else: return (chainage * long_rtss)/self.chainage_f
    
    def getChainageFromLong (self, longueur):
        """ 
        Méthode qui retourne le chainage correspondant à la longueur demandé le long du RTSS
        Distance géometrique --> Chaînage
        
        Args:
            - longueur (float/int): La longueur géometrique à corriger le long du RTSS
        
        Return:
            - chainage_corriger (float/int): Le chainage correspondant à la longueur en entrée
        """
        # Longueur du RTSS
        long_rtss = self.geometry.length()
        # Retourner le chainage de fin si la longueur est plus grande que la longueur du RTSS
        if longueur >= long_rtss: return self.chainage_f
        # Si la longueur est plus petit que le chainage de début du RTSS retourner le chainage de début du RTSS
        elif longueur <= self.chainage_d: return self.chainage_d 
        else: return (longueur * self.chainage_f)/ long_rtss

    def getTransect (self, chainage, dist_d, dist_g, inverse=False):
        """
        Méthode qui crée une ligne perpendiculaire au RTSS.
        Par défault le transect est de gauche => droite, mais peut être inversé droite => gauche.

        Args:
            - chainage (real/str) = Chainage du transect. Peut être formater ex: (2+252 ou 2252)
            - dist_d (real) = Longueur du transect à droite.
            - dist_g (real) = Longueur du transect à gauche.
            - inverse (bool) = Sense du transect True:[droite => gauche] False:[gauche => droite]
        
        Return:
            - transect (QgsGeometry) = La géometrie linéaire du transect
        """
        # Point à droite du RTSS
        pt_droit = self.getPointFromChainage(chainage, dist_d)
        # Point à gauche du RTSS
        pt_gauche = self.getPointFromChainage(chainage, dist_g*-1)
        # Inverser les points si spécifié
        if inverse: pt_droit, pt_gauche = pt_gauche, pt_droit
        # Retourner la ligne entre les deux points
        return QgsGeometry().fromPolylineXY([pt_gauche.asPoint(), pt_droit.asPoint()])
    
    def getAngleAtChainage(self, chainage):
        """
        Méthode qui permet de retourner l'angle le long de la ligne à un chainage.

        Args:
            - chainage (str/real): Le chainage pour lequel mesurer l'angle
        """
        # Vérifier chainage 
        chainage = verifyFormatChainage(chainage)
        # Longueur géometrique correspondant au chainage
        long = self.getLongFromChainage(chainage)
        # Angle en radian du RTSS au chainage dans le sense horraire par raport au Nord
        angle = self.geometry.interpolateAngle(long)
        # Retourner l'angle en degrees
        return math.degrees(angle)
    
    def interpolateOffsetAtChainage(self, chainage, chainage_d, chainage_f, offset_d, offset_f):
        """
        Méthode qui permet de calculer le offset d'une ligne à un chainage par rapport au RTSS.

        Args:
            - chainage (str/real): Le chainage pour lequel interpoler le offset
            - chainage_d (str/real): Le chainage de début de la ligne
            - chainage_f (str/real): Le chainage de fin de la ligne
            - offset_d (real): Le offset de début de la ligne
            - offset_f (real): Le offset de fin de la ligne
        """
        if chainage_d == chainage_f: return None
        if offset_d == offset_f: return offset_d
        
        long_d = self.getLongFromChainage(chainage_d)
        long_f = self.getLongFromChainage(chainage_f)
        long = self.getLongFromChainage(chainage)
        # Différence du offset
        offset_diff = offset_f - offset_d
        # Longueur de la nouvelle ligne
        longueur_ligne = long_f - long_d
        # Retourner le offset de la ligne à la position du chainage
        return (((long-long_d) * offset_diff)/longueur_ligne) + offset_d
    
    def isChainageOnRTSS(self, chainage):
        """ Méthode qui permet de vérifier si le chainage est valide pour le RTSS """
        return chainage >= self.chainage_d and chainage <= self.chainage_f
    
    def setPointRTSS(self, chainage, offset=0):
        """ Méthode qui permet de créer un PointRTSS """
        if chainage is None or offset is None: return None
        return PointRTSS(self.getRTSS(), self.getChainageOnRTSS(chainage), offset)

class geocodage:
    """ Une class qui permet d'éffectuer des oppérations de géocodage à partir d'une couche de RTSS. """
    
    def __init__ (self, rtss_features, crs, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, precision=0, interpolate_on_rtss=True):
        """ 
        Initialisation de la class de géocodage avec une couche contenant les RTSS à utiliser.
        La class conserve en mémoire seulement les geometries et les informations des deux champs.
        L'instance du QgsVectorLayer peut donc être supprimé sans problème. 
        
        * Les valeurs par défault sont les noms des champs de la couche BGR - RTS du WFS 
        Args:
            - rtss_features(QgsFeaturesIterator): La couche des RTSS
            - crs (QgsCoordinateReferenceSystem): Le sytème de coordonnée de la couche
            - nom_champ_rtss (str): Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int): Précison du chainage, Nombre de chiffre après la virgule
            - interpolate_on_rtss (bool): L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
        """
        # Nom des champs de la couche RTSS
        self.nom_champ_rtss = nom_champ_rtss
        self.nom_champ_long = nom_champ_long
        self.nom_champ_chainage_d = nom_champ_chainage_d
        self.setPrecision(precision)
        self.setInterpolation(interpolate_on_rtss)
        # Référence des RTSS
        self.dict_rtss = {}
        # Référence des id RTSS
        self.dict_ids = {}
        # Référence du system de coordonnée
        self.setCRS(crs)
        # Créer la référence des RTSS
        self.updateReferenceDesRTSS(rtss_features)
    
    @classmethod
    def fromLayer(cls, layer, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, precision=0, interpolate_on_rtss=True):
        """ 
        Constructeur avec la couche QgsVectorLayer des RTSS
        
        Args:
            - layer (QgsVectorLayer): La couche des RTSS
            - nom_champ_rtss (str): Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int): Précison du chainage, Nombre de chiffre après la virgule
            - interpolate_on_rtss (bool): L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
        """
        if isinstance(layer, QgsVectorLayer): return cls(layer.getFeatures(), layer.crs(), nom_champ_rtss, nom_champ_long, nom_champ_chainage_d, precision, interpolate_on_rtss)
        else: return cls(None, None)
    
    """ Constructeur avec le nom de la couche des RTSS dans le projet courrant """
    @classmethod
    def fromProject(cls, layer_name=DEFAULT_NOM_COUCHE_RTSS, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, precision=0, interpolate_on_rtss=True):
        """ 
        Constructeur avec le nom de la couche des RTSS dans le projet courrant
        
        Args:
            - layer_name (str): Le nom de la couche des RTSS dans le projet
            - nom_champ_rtss (str): Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int): Précison du chainage, Nombre de chiffre après la virgule
            - interpolate_on_rtss (bool): L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
        """
        layer = validateLayer(layer_name, [nom_champ_rtss, nom_champ_long], geom_type=1)
        if layer: return cls(layer.getFeatures(), layer.crs(), nom_champ_rtss, nom_champ_long, nom_champ_chainage_d, precision, interpolate_on_rtss)
        else: return cls(None, None)
    
    def __repr__ (self): return f"Geocodage ({len(self.dict_rtss)} RTSS)"
        
    def isEmpty(self): 
        """ Méthode qui retourne l'indicateur le l'instantiation de la class. Retourn True tant que la class n'a pas des RTTS valide"""
        return self.dict_rtss == {}
    
    def updateReferenceDesRTSS(self, rtss_features, crs=None, nom_champ_rtss=None, nom_champ_long=None, nom_champ_chainage_d=None):
        """ Méthode qui permet de créer ou de mettre à jour la référence des RTSS
        
        Entrée:
            - rtss_features(QgsFeaturesIterator): La nouvelle couche des RTSS
            - crs (QgsCoordinateReferenceSystem): Le système de coordonnée de la couche
            - nom_champ_rtss (str): Le nom du champ contenant les numéros des RTSS
            - nom_champ_long (str): Le nom du champ contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str): Le nom du champ contenant le chainage de début du RTSS
        """
        # Modifier la référence du nom du champs si un nouveau nom est défini
        if nom_champ_rtss: self.nom_champ_rtss = nom_champ_rtss
        if nom_champ_long: self.nom_champ_long = nom_champ_long
        self.nom_champ_chainage_d = nom_champ_chainage_d
        # Définir le nouveau CRS si défini
        if crs: self.setCRS(crs)
        # Vérifier que le CRS de la class est valide
        if self.getCrs() and rtss_features:
            # Index spatial des géometries des RTSS
            self.spatial_index = QgsSpatialIndex(flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
            # Parcourir toutes les entités de la couche des RTSS
            for rtss in rtss_features:
                # Numéro du RTSS
                num_rts = rtss[self.nom_champ_rtss]
                # Créer un instance de la class featRTSS
                self.dict_rtss[num_rts] = featRTSS.fromFeature(rtss, nom_champ_rtss=self.nom_champ_rtss, nom_champ_long=self.nom_champ_long, chainage_d=self.nom_champ_chainage_d)
                self.dict_ids[rtss.id()] = num_rts
                self.spatial_index.addFeature(rtss)
            
    def getEpsg(self):
        """ Retourne le EPSG courrant de l'object """ 
        if isinstance(self.crs, QgsCoordinateReferenceSystem): return self.crs.authid()
        else: return None
    
    def getCrs(self):
        """ Retourne le CRS courrant de l'object """
        return self.crs
    
    def getPointOnRTSS(self, point, formater_rtss=False, formater_chainage=False):
        """
        Méthode qui permet de retourner le point le plus proche sur le RTSS à partir d'un point.

        Args:
            - point (QgsGeometry/QgsPointXY): Le point pour lequel faire l'analyse
            - formater_rtss (bool): Formater le numéro de RTSS en sortie
            - formater_chainage (bool): Formater le chainage en sortie

        Return:
            - list: [La geometry du point sur le RTSS, numéro de RTSS, chainage, distance]
        """
        # Vérifier le format du point
        point = verifyFormatPoint(point)
        # Trouver le RTSS le plus proche
        dict_res = self.nearestRTSS(point)[0]
        # featRTSS du RTSS à proximité
        feat_rtss = dict_res['rtss']
        # Trouver le chainage du point sur le RTSS
        chainage = feat_rtss.getChainageFromPoint(point)
        
        # Formater et arrondir le chainage 
        if formater_chainage: chainage = formaterChainage(chainage, self.precision)
        else: chainage = round(chainage, self.precision)
        # Trouver le point correspondant au chainage sur le RTSS
        point_on_rtss = feat_rtss.getPointFromChainage(chainage)
        # Le RTSS 
        rtss = feat_rtss.getRTSS(formater_rtss)
        # Retourner une liste des informations trouvé
        return [point_on_rtss, rtss, chainage, dict_res['distance']]
    
    def getRTSS(self, rtss, rtss_complet=True):
        """ 
        Fonction qui retourne l'instance de la class featRTSS pour un RTSS.
        Retourne une valeur vide si le RTSS n'existe pas.
        
        Args:
            - rtss(str): Le numéro de RTSS à chercher
            - rtss_complet (bool): Le numéro de RTSS est complet 
            
        Return:
            - featRTSS: L'objet featRTSS du RTSS
        """ 
        rtss = verifyFormatRTSS(rtss)
        # Retourner la classe featRTSS si le RTSS existe dans le dictionnaire
        if rtss in self.dict_rtss and rtss_complet: return self.dict_rtss[rtss]
        elif not rtss_complet:
            rtss_possible = []
            for key in self.dict_rtss.keys():
                if rtss == key[:len(rtss)] or "000" + rtss == key[:len(rtss)+3] or "00" + rtss == key[:len(rtss)+2]:
                    rtss_possible.append(self.dict_rtss[key])
            return rtss_possible
        return None
    
    def getRTSSFromPoint(self, point):
        self.getRTSS(point.getRTSS())
    
    def getRTSSFromId(self, id):
        # Vérifier si le RTSS existe dans le dictionnaire 
        if id in self.dict_ids:
            num_rtss = self.dict_ids[id]
            return self.dict_rtss[num_rtss]
        else: return None
    
    def getListRTSS(self, formater=False, sorted=False):
        """
        Méthode qui permet de retourner la liste de toutes les numéros de RTSS du module de géocodage

        Args:
            - formater (bool): Formater les numéros de RTSS
            - sorted (bool): Ordonner en ordre croissant la liste des RTSS
        """
        # Liste de toutes les RTSS
        list_rtss = list(self.dict_rtss.keys())
        # Formater la liste si nécéssaire
        if formater: list_rtss = [formaterRTSS(rtss) for rtss in list_rtss]
        # Trier la liste si nécéssaire
        if sorted: list_rtss.sort()
        # Retourner la liste
        return list_rtss
        
    def getListFeatRTSS(self):
        """ Méthode qui permet de retourner la liste de toutes les objets featRTSS du module de géocodage """
        # Retourner la liste de toutes les featRTSS
        return list(self.dict_rtss.values())
            
    def geocoder(self, rtss, chainage, chainage_f=None, offset=0, offset_f=None, chainage_d2=None, chainage_f2=None, offset_d2=None, offset_f2=None, reverse=False):
        """
        Méthode qui renvoie une géometrie à partir d'un RTSS/chainage.
        Elle peut géocoder des geometries ponctuelle, linéaire ou surfacique.
        Les géometries linéaire peuvent avoir un offset. Si seulement un offset est définie ou
        que les deux offset sont pareille, la ligne vas être parallel au RTSS. Si deux offset sont défini,
        La difference entre les deux offset vas être répartie sur la longeur de la ligne. 
        
        Args:
            - rtss (str): Le numéro du RTSS. Peut être formater ex: (0001002155000D ou 00010-02-155-000D)
            - chainage (real/str): Le chainage de début. Peut être formater ex: (2+252 ou 2252)
            - chainage_f (real/str): Le chainage de fin. Peut être formater ex: (2+252 ou 2252)
            - offset (real): Le offset de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f (real): Le offset de fin de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - reverse (bool): Inverser la géometrie
        
        Return:
            - QgsGeometry: La géometrie géocoder
        """
        # Instance de la class featRTSS contenant toute les informations du RTSS
        feat_rtss = self.getRTSS(rtss)
        # Geometry vide
        geom = QgsGeometry()
        # Vérifier que le RTSS est dans la référence des RTSS
        if feat_rtss:
            # Le géocodage est ponctuelle si seulement le chainage de fin et le offset de fin ne sont pas défini ou égale au chainage de début
            if (chainage_f is None or chainage == chainage_f) and (offset == offset_f or offset_f is None):
                # Géocoder le point sur le RTSS
                geom = feat_rtss.getPointFromChainage(chainage, offset)
            # Le géocodage est linéaire si les paramètres pour les polygones sont tous NULL 
            elif [chainage_d2, chainage_f2, offset_d2, offset_f2].count(None) == 4:
                # Géocoder la ligne
                geom = feat_rtss.getLineFromChainage(chainage, chainage_f, offset_d=offset, offset_f=offset_f, reverse_geom=reverse)
            # Sinon le géocodage est polygonal
            else: geom = feat_rtss.getPolygonFromChainage(
                    chainage_d1=chainage, chainage_f1=chainage_f, offset_d1=offset, offset_d2=offset_d2,
                    chainage_d2=chainage_d2, chainage_f2=chainage_f2, offset_f1=offset_f, offset_f2=offset_f2,
                    iterpolate_middle=self.interpolate_on_rtss)
        # Retourner la géometries géocoder
        return geom
    
    def geocoderPoint(self, point):
        feat_rtss = self.getRTSSFromPoint(point)
        # Geometry vide
        geom = QgsGeometry()
        # Géocoder le point sur le RTSS
        if feat_rtss: geom = feat_rtss.getPoint(point)           
        # Retourner la géometries géocoder
        return geom
    
    def geocoderLine(self, list_points, reverse=False):
        # Geometry vide
        geom = QgsGeometry()
        line = []
        for idx, point in enumerate(list_points):
            feat_rtss = self.getRTSSFromPoint(point)
            if not feat_rtss: return geom
            if idx == len(list_points) - 1 or not self.interpolate_on_rtss:
                line.append(feat_rtss.getPoint(point).asPoint())
            else:
                next_point = list_points[idx+1]
                next_feat_rtss = self.getRTSSFromPoint(next_point)
                if not next_feat_rtss: return geom
                if feat_rtss != next_feat_rtss: return geom
                #reverse_geom = point.getChainage() > next_point.getChainage()
                ligne = feat_rtss.getLineFromChainage(
                    point.getChainage(), next_point.getChainage(),
                    point.getOffset(), next_point.getOffset(),
                    iterpolate_middle=self.iterpolate_middle, reverse_geom=reverse).asPolyline()
                list_polygon_points += ligne[:-1]
        # Retourner la géometries géocoder
        return geom
    
    def geocoderInverse(self, geometry, rtss=None, formater_rtss=False, formater_chainage=False):
        """
        Méthode qui associe un RTSS/chainage à une géometrie ponctuelle ou linéaire. Un RTSS peux être spécifié
        s'il est connue. Sinon le RTSS le plus proche est selectionnée. Pour selectionnée le RTSS le plus proche,
        d'un entités linéaire, c'est la sum des distance avec le point de début et de fin.
        
        Args:
            - geometry (QgsGeometry): La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            - rtss(str): Le numéro du RTSS. Peut être formater ex: (0001002155000D ou 00010-02-155-000D)
            - formater_rtss (bool): Idicateur pour formater le résultat du RTSS
            - formater_chainage (bool): Idicateur pour formater les résultat des chainage
        
        Return:
            - dict: {'rtss': numéro du RTSS, 'chainage_d': Chainage de début, 'chainage_f': Chainage de fin}
        """
        # Vérifier que le RTSS est dans la bonne manière
        if rtss: rtss = verifyFormatRTSS(rtss)
            
        # Aller chercher directement le featRTSS si un RTSS est défini et est dans la dictionnaire de référence
        if rtss in self.dict_rtss: feat_rtss = self.dict_rtss[rtss]
        # Sinon appeller la fonction pour avoir le RTSS le plus proche de la géometrie
        else: feat_rtss = self.nearestRTSS(geometry)[0]['rtss']
        
        # Liste des chainages les plus proche de chacun des vertex de la ligne en entrée 
        list_chainage = [feat_rtss.getChainageFromPoint(QgsPointXY(vertex.x(), vertex.y())) for vertex in geometry.vertices()]
        
        # Formater les chainage si spécifié
        if formater_chainage:
            chainage_min = formaterChainage(min(list_chainage), self.precision)
            chainage_max = formaterChainage(max(list_chainage), self.precision)
        else:
            chainage_min = round(min(list_chainage), self.precision)
            chainage_max = round(max(list_chainage), self.precision)
        
        # Retourne le dictionnaire avec les résultat des RTSS, chainage_d et chainage_f
        return {'rtss': feat_rtss.getRTSS(formater=formater_rtss), 'chainage_d': chainage_min, 'chainage_f': chainage_max}
    
    def geocoderInversePoint(self, geom_point, rtss=None, get_offset=False, concatenante=False, formater_rtss=False, formater_chainage=False):
        """
        Méthode qui permet d'associer un RTSS/chainage à une géometrie ponctuelle. 
        Un RTSS peux être spécifié s'il est connue. Sinon le RTSS le plus proche est selectionnée.

        Args:
            - geom_point (QgsGeometry): La géometry du point à analyser
            - rtss (str): Numéro de RTSS du point à analyser
            - get_offset (bool): Retourner le offset
            - concatenante (bool): Retourner seulement 1 résultat
            - formater_rtss (bool): Formater les RTSS résultant
            - formater_chainage (bool): Formater les chainages résultant
        
        Return:
            - [concatenante = True] list: [{"rtss": numéro du rtss, "chainage": chainage du point, "offset": la distance du RTSS}, ...]
            - [concatenante = False] dict: {"rtss": numéro du rtss, "chainage": chainage du point, "offset": la distance du RTSS}
        """
        # Vérifier que le RTSS est dans la bonne manière
        if rtss: rtss = verifyFormatRTSS(rtss)
        # Vérifier si un RTSS est défini et est dans la dictionnaire de référence
        if rtss in self.dict_rtss: feats_rtss = [self.dict_rtss[rtss]]
        # Sinon appeller la fonction pour avoir le RTSS le plus proche de la géometrie
        else: feats_rtss = [res['rtss'] for res in self.nearestRTSS(geom_point, nbr=int(not concatenante))]
        
        results = []
        for feat_rtss in feats_rtss:
            # Définir le chainage
            chainage = round(feat_rtss.getChainageFromPoint(geom_point.asPoint()), self.precision)
            # Formater les chainage si spécifié
            if formater_chainage: chainage = formaterChainage(chainage, self.precision)
            # Dictionnaire avec les résultat du RTSS et chainage 
            result = {"rtss": feat_rtss.getRTSS(formater=formater_rtss), "chainage": chainage}
            # Ajouter le offset si spécifié
            if get_offset: result["offset"] = feat_rtss.getDistanceFromPoint(geom_point.asPoint())
            results.append(result)
        
        if concatenante: return results
        else: return results[0]
        
    def geocoderInverseLineByExtremities(self, geom_line, rtss=None, get_offset=False, concatenante=False, formater_rtss=False, formater_chainage=False):
        """
        Méthode qui permet de trouver le RTSS, chainage et offset des extremitées d'une ligne.

        Args:
            - geom_line (QgsGeometry): La géometry du point à analyser
            - rtss (str): Numéro de RTSS du point à analyser
            - get_offset (bool): Retourner le offset
            - concatenante (bool): Retourner seulement 1 résultat
            - formater_rtss (bool): Formater les RTSS résultant
            - formater_chainage (bool): Formater les chainages résultant
        
        Return:
            - [concatenante = True] dict: {"start": [{"rtss": numéro du rtss début, "chainage": chainage de début, "offset": la distance du RTSS}, ...], "end":...}
            - [concatenante = False] dict: {"start": {"rtss": numéro du rtss, "chainage": chainage du point, "offset": la distance du RTSS}, "end":...}
        """
        # Dictionnaire des resultats des extremitées
        results = {}
        # Parcourir les deux extremitées de la géometrie linéaire
        for extrem, idx1, idx2 in [["start", 0, 1], ["end", -1, -2]]:
            # Géocodage inverse de l'extremitées
            result = self.geocoderInversePoint(
                QgsGeometry.fromPointXY(geom_line.asPolyline()[idx1]), rtss=rtss, get_offset=get_offset,
                concatenante=True, formater_rtss=formater_rtss, formater_chainage=formater_chainage)
            # Vérifier s'il y a plus d'un RTSS à la même distance de l'extremitées
            if len(result) > 1 and not concatenante: 
                # Géocodage inverse du point précédant l'extremitées
                result_rtss = self.geocoderInversePoint(QgsGeometry.fromPointXY(geom_line.asPolyline()[idx2]), rtss=rtss, get_offset=False, concatenante=False, formater_rtss=formater_rtss)
                # S'assurer que le RTSS du point précédant est dans les resultats de l'extremitées
                if result_rtss["rtss"] in [r["rtss"] for r in result]:
                    # Refaire le géocodage inverse de l'extremitées avec le RTSS spécifique
                    result = [self.geocoderInversePoint(
                        QgsGeometry.fromPointXY(geom_line.asPolyline()[idx1]), rtss=result_rtss["rtss"], get_offset=get_offset,
                        concatenante=False, formater_rtss=formater_rtss, formater_chainage=formater_chainage)]
                # Sinon on peux rien faire... 
                else: result = [result[0]]
            # Ajouter le resultat
            results[extrem] = result
        
        return results
    
    
    def geocoderInverseLineByVertex(self, geom_line, rtss=None, get_offset=False, concatenante=False, formater_rtss=False, formater_chainage=False):
        """
        Méthode qui permet de trouver le RTSS, chainage et offset pour chaque vertex d'une ligne.

        Args:
            - geom_line (QgsGeometry): La géometry du point à analyser
            - rtss (str): Numéro de RTSS du point à analyser
            - get_offset (bool): Retourner le offset
            - concatenante (bool): Retourner seulement 1 résultat
            - formater_rtss (bool): Formater les RTSS résultant
            - formater_chainage (bool): Formater les chainages résultant
        
        Return:
            - [concatenante = True] list: [[{"rtss": numéro du rtss début, "chainage": chainage de début, "offset": la distance du RTSS}, ...], ...]
            - [concatenante = False] dict: [{"rtss": numéro du rtss, "chainage": chainage du point, "offset": la distance du RTSS}, ...]
        """
        list_values = []
        for vertex in geom_line.vertices():
            # Ajouter la valeur RTSS, chainage et offset du vertex
            list_values.append(self.geocoderInversePoint(
                QgsGeometry.fromPointXY(QgsPointXY(vertex.x(), vertex.y())),
                rtss=rtss,
                get_offset=get_offset,
                concatenante=concatenante,
                formater_rtss=formater_rtss,
                formater_chainage=formater_chainage))
        # Dictionnaire avec les résultat des RTSS, chainage_d et chainage_f
        return list_values
    
    def nearestRTSS(self, geometry, nbr=1, dist_max=0):
        """
        Méthode pour determiner les featRTSS, dans la référence des RTSS, les plus proche d'une geometrie.
        La géometrie peut être ponctuelle ou linéaire. Pour identifier le RTSS le plus proche d'une ligne,
        la moyenne des distance avec le point de début et de fin est utiliser. Cela permet de ne pas retourner 
        un RTSS qui croise une ligne à une place alors que la ligne est clairement parallel à un autre RTSS.
        
        Args:
            - geometry (QgsGeometry): La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            - nbr (int): Nombre de RTSS à proximité à retourner
            - dist_max (int): Distance maximum à tolérer pour la recherche (0=Aucune)
            
        Return:
            - liste: [{'rtss': Objet featRTSS, 'distance': distance du RTSS}, ...]
        """
        # Définir le nombre de voisin à trouver
        nbr_neighbors = nbr if nbr != 0 else 1
        list_nearest_rtss = []
        # Type de geometry (1 = Point et 2 = Ligne)
        geometry_type = geometry.wkbType()
        # Parcourir la liste des id de RTSS les plus proche de la geometrie en entrée
        for id in self.spatial_index.nearestNeighbor(geometry, neighbors=nbr_neighbors, maxDistance=dist_max):
            feat_rtss = self.getRTSSFromId(id)
            # La géometrie du RTSS
            rtss_geom = feat_rtss.getGeometry()
            # Distance entre le point et le rtss
            if geometry_type == 1: dist = rtss_geom.distance(geometry)
            elif geometry_type == 2:
                # Liste des points de la ligne
                line = geometry.asPolyline()
                # Moyenne des distance du premier et du dernier point de la ligne avec le RTSS
                dist = sum([rtss_geom.distance(QgsGeometry().fromPointXY(pt)) for pt in [line[0], line[-1]]])/2
            
            if dist <= dist_max or dist_max == 0 : list_nearest_rtss.append({'rtss':feat_rtss, 'distance':dist})
                
        list_nearest_rtss.sort(key=lambda rtss : rtss['distance'])
        # Retourner la class featRTSS du RTSS le plus proche
        if nbr == 0: return list_nearest_rtss
        else: return list_nearest_rtss[:nbr_neighbors]
            
    def getAngleAtChainage(self, rtss, chainage):
        """
        Méthode qui permet de retourner l'angle le long de la ligne à un chainage.

        Args:
            - rtss (str): Le numéro du RTSS
            - chainage (str/real): Le chainage pour lequel mesurer l'angle
        """
        # Instance de la class featRTSS contenant toute les informations du RTSS
        feat_rtss = self.getRTSS(rtss)
        # Retourner l'angle au chainage pour le RTSS
        if feat_rtss: return feat_rtss.getAngleAtChainage(chainage)
        else: return None
    
    def setCRS(self, crs):
        """
        Méthode qui permet de définir le système de coordonnée des geometries utilisé. 
        Il doit être un instance de la class QgsCoordinateReferenceSystem de QGIS et avoir une projection en mètre
        
        Args:
            - crs (QgsCoordinateReferenceSystem): Le système de coordonnée des géometries des RTSS
        """
        self.crs = None
        if isinstance(crs, QgsCoordinateReferenceSystem):
            self.crs = crs
            self.epsg = self.crs.authid()
            # La couche des RTSS doit être projeté dans une projection en mètre
            if self.crs.mapUnits() != 0: raise Exception("L'unité de la couche des RTSS doit être en mètre.")
    
    def setPrecision(self, precision):
        """
        Méthode pour définir la précision des chainages à retourner.
        
        Args:
            - precision (int): La valeur pour l'arrondi (entier positif = nbr décimal / entier négatif = la dizaine)
        """
        if isinstance(precision, int): self.precision = precision
    
    def setInterpolation(self, interpolate_on_rtss):
        """ Méthode pour définir l'indicateur d'interpolation. """
        self.interpolate_on_rtss = interpolate_on_rtss

    """ 
    Source:
        Polystrip plugin:
            begin                : 2017-07-29
            git sha              : $Format:%H$
            copyright            : (C) 2017 by Werner Macho
            email                : werner.macho@gmail.com 
        following code mostly taken from
        https://gis.stackexchange.com/questions/173127/generating-equal-sized-polygons-along-line-with-pyqgis
    """
    def getAtlasLayer(self, list_start_points, width, height, list_end_points=[], overlap=20, start_offset=10, vertical_margin=10, chainage_exact=False):
        """
        Méthode qui permet de générer des polygones le long d'un RTSS. 
        Ces polygon sont concu pour être utiliser comme atlas pour une carte. Ils sont placer de manière 
        à s'assurer que toutes le RTSS contenue dans le polygon est entièrement contenu à l'interieur du polygon. 

        Args:
            - list_start_points (list): Liste des objets PointRTSS des débuts d'atlas
            - width (float): Largeur des polygones en mètres
            - height (float): Hauteur des polygones en mètres
            - list_end_points (list): Liste des objets PointRTSS des fins d'atlas
            - overlap (int): Pourcentage de recouvrement entre les polygons
            - start_offset (int): Pourcentage de la longeurs du premier polygone qui est décaler pour convrir le début
            - vertical_margin (int): Pourcentage de la hauteur des marges verticales que le RTSS ne doit pas dépasser
            - chainage_exact (bool): Déterminer les chainages excate des débuts/fin des polygons

            Return: 
                - QgsVectorLayer: La couche contenant toutes les entitées des pages d'atlas
        """
        # Create the atlas pages layer
        layer_pages = QgsVectorLayer(f"Polygon?crs={str(self.getEpsg())}", "Atlas_pages", "memory")
        field_chainage_type = QVariant.Int if self.precision == 0 else QVariant.Double
        # Ajouter les champs de la couche
        attributes = [
            QgsField("rtss", QVariant.String),
            QgsField("chainage_d", field_chainage_type),
            QgsField("chainage_f", field_chainage_type),
            QgsField("angle", QVariant.Double)]
        layer_pages.dataProvider().addAttributes(attributes)
        layer_pages.updateFields()
        
        page_features = []
        for i, start in enumerate(list_start_points):
            end = list_end_points[i] if i < len(list_end_points) else None
            # Parcourir les informations des pages de l'atlas
            for page in self.getAtlasPages(start, width, height, end=end, overlap=overlap, start_offset=start_offset, vertical_margin=vertical_margin, chainage_exact=chainage_exact):
                # Create new page feature
                feat = QgsFeature()
                feat.setAttributes(list(page["atts"].values()))
                feat.setGeometry(page["geom"])
                page_features.append(feat)
        if page_features: layer_pages.dataProvider().addFeatures(page_features)
        # Retourner la couche 
        return layer_pages
    
    def getAtlasPages(self, start, width, height, end=None, overlap=20, start_offset=10, vertical_margin=10, chainage_exact=False):
        """
        Méthode qui permet de générer des polygones le long d'un RTSS. 
        Ces polygon sont concu pour être utiliser comme atlas pour une carte. Ils sont placer de manière 
        à s'assurer que toutes le RTSS contenue dans le polygon est entièrement contenu à l'interieur du polygon. 

        Args:
            - start (PointRTSS): PointRTSS du débuts de l'atlas
            - width (float): Largeur des polygones en mètres
            - height (float): Hauteur des polygones en mètres
            - end (PointRTSS): PointRTSS de la fin de l'atlas
            - overlap (int): Pourcentage de recouvrement entre les polygons
            - start_offset (int): Pourcentage de la longeurs du premier polygone qui est décaler pour convrir le début
            - vertical_margin (int): Pourcentage de la hauteur des marges verticales que le RTSS ne doit pas dépasser
            - chainage_exact (bool): Déterminer les chainages excate des débuts/fin des polygons

            Return: 
                - dict: [{"atts": {"rtss": RTSS, "chainage_d": chainage de début, "chainage_f": chainage de fin, "angle": l'angle de la page}, "geom": La geometry de la page}, ...]
        """
        # BUG: La vérification que le rtss est entièrement couvert est valide seulement de manière vertical.
        atlas_pages_info = []
        rtss = start.getRTSS()
        # Instance de la class featRTSS contenant toute les informations du RTSS
        feat_rtss = self.getRTSS(rtss)
        # Vérifier que le RTSS est dans la référence des RTSS
        if not feat_rtss: return atlas_pages_info
        # Créer un point a la fin du RTSS si aucun point n'a été fait
        if not end: end = PointRTSS(rtss, feat_rtss.getChainageFin())
        
        # Définir les informations de la ligne
        geometrie = feat_rtss.getLineFromChainage(start.getChainage(), end.getChainage())
        extended_geom = QgsGeometry.extendLine(geometrie, (start_offset/100) * width, (start_offset/100) * width)
        geom_length = extended_geom.length() 
        # Position du curseur en pourcentage (0 à 1)
        curs, forward = 0, 0
        # Définir le pas entre chaque page (0 à 1)
        step = 1.0 / (geom_length / width)
        # Définir la distance maximun entre le center vertical du polygon et ça hauteur
        tolerance_margin = (1.0 - (vertical_margin/100)) * (height/2)
        # Définir le pas de reculons entre chaque page pour avoir le overlap (0 à 1)
        stepnudge = (1.0 - (overlap/100))
        while curs <= 1 and forward < 1:
            # Get the first point for the polygon
            start_point = extended_geom.interpolate(curs * geom_length)
            # Definir la modification du pas à appliquer si la page de couvre pas la ligne
            best_step = 1
            # Distance maximum du RTSS et du centre vertical de la page
            vertical_dist_max = tolerance_margin
            # Continuer tant que la distance maximum est plus grande que la tolérance
            while vertical_dist_max >= tolerance_margin and best_step > 0.1:
                # Définir la position du point de fin 
                forward = curs + (best_step * step)
                # Position maximal est de 1
                if forward > 1: forward = 1
                # Définir le point de fin
                end_point = extended_geom.interpolate(forward * geom_length)
                # Définir la liste des points de la partie du RTSS utiliser pour générer la page
                line_geom = [start_point.asPoint()]
                for i, vertice in enumerate(extended_geom.vertices()):
                    # Vertex sous forme de geometry
                    vertice_geom = QgsGeometry().fromPointXY(QgsPointXY(vertice.x(),vertice.y()))
                    current_dist = extended_geom.lineLocatePoint(vertice_geom)
                    if current_dist >= extended_geom.lineLocatePoint(end_point): break
                    elif current_dist > extended_geom.lineLocatePoint(start_point): line_geom.append(vertice_geom.asPoint())
                line_geom.append(end_point.asPoint())
                # Extract x and y coordinates from points
                x_coords, y_coords = [point.x() for point in line_geom], [point.y() for point in line_geom]
                # Perform linear regression
                slope, intercept, _, _, _ = linregress([x_coords[0], x_coords[-1]], [y_coords[0], y_coords[-1]])
                # Calculate distances maximum from each point to the regression line
                vertical_dist_max = max([abs(y - (slope * x + intercept)) / np.sqrt(slope**2 + 1) for x, y in zip(x_coords, y_coords)])
                best_step -= 0.1
                
            # Construire la geometrie de la page
            page_geom = QgsGeometry().fromWkt('POLYGON((0 0, 0 {height},{width} {height}, {width} 0, 0 0))'.format(height=height, width=width))
            page_geom.translate(0, -height/2)
            currangle = (start_point.asPoint().azimuth(end_point.asPoint())+270) % 360
            page_geom.rotate(currangle, QgsPointXY(0, 0))
            page_geom.translate(start_point.asPoint().x(), start_point.asPoint().y())
            page_geom.asPolygon()
            
            chainage_d = round(feat_rtss.getChainageFromPoint(start_point), self.precision)
            chainage_f = round(feat_rtss.getChainageFromPoint(end_point), self.precision)
            if chainage_exact:
                # Intersections entre le périmètre de la page et le RTSS
                intersection = feat_rtss.getGeometry().intersection(QgsGeometry.fromPolylineXY(page_geom.asPolygon()[0]))
                if intersection:
                    # Calculer les valeurs de chainages des points d'intersections
                    if intersection.wkbType() == QgsWkbTypes.MultiPoint: intersect_list = sorted([round(feat_rtss.getChainageFromPoint(point), self.precision) for point in intersection.asMultiPoint()])
                    else: intersect_list = [round(feat_rtss.getChainageFromPoint(intersection.asPoint()), self.precision)]
                    # Liste des chainages plus grand que celui de début
                    chainages_potentiel_f = [chainage for chainage in intersect_list if chainage > chainage_d]
                    if len(chainages_potentiel_f) != 0: chainage_f = chainages_potentiel_f[0]
            # Create new page info
            page_info = {"atts": {"rtss": rtss, "chainage_d": chainage_d, "chainage_f": chainage_f, "angle": currangle}, "geom": page_geom}
            atlas_pages_info.append(page_info)
            # Advance current position
            curs += stepnudge * best_step * step
            
        return atlas_pages_info



class PointRTSS:
    """ Une définition d'un point selon le référencement linéaire RTSS/chainage"""
    
    __slots__ = ("rtss", "chainage", "offset")
    
    def __init__ (self, rtss, chainage, offset=0):
        self.setRTSS(rtss)
        self.setChainage(chainage)
        self.setOffset(offset)
    
    def __str__ (self): return f"{self.rtss} ({self.chainage}, {self.offset})"
    
    def __repr__ (self): return f"PointRTSS {self.rtss}: ({self.chainage} ({self.offset}m))"

    def getChainage(self, formater=False):
        if formater: return formaterChainage(self.chainage)
        else: return self.chainage
        
    def getOffset(self):
        return self.offset
    
    def getRTSS(self, formater=False):
        if formater: return formaterRTSS(self.rtss)
        else: return self.rtss
    
    def setChainage(self, chainage):
        self.chainage = verifyFormatChainage(chainage)
        
    def setOffset(self, offset):
        self.offset = offset
    
    def setRTSS(self, rtss):
        self.rtss = verifyFormatRTSS(rtss)


pass