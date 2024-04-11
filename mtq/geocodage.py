# -*- coding: utf-8 -*-

# Importer les objects du module core de QGIS 
from qgis.core import (QgsGeometry, QgsPointXY, QgsProject, QgsGeometryUtils, QgsPoint, QgsVectorLayer,
                        QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsSpatialIndex, QgsFeature,
                        QgsField)
from qgis.PyQt.QtCore import QVariant

# Importer les fonction de formatage du module
from .format import (verifyFormatRTSS, verifyFormatChainage, verifyFormatPoint,
                    formaterChainage, formaterRTSS)
from .fnt import validateLayer
# Importer la librairie pour des opérations trigo
import math
import itertools


# ======================== Nom des options par défault ============================
# Nom de la couche des RTSS 
DEFAULT_NOM_COUCHE_RTSS = 'BGR - RTSS'
# Nom du champ qui contient les RTSS 
DEFAULT_NOM_CHAMP_RTSS = 'num_rts'
# Nom du champ qui contient le chainage de début (None pour vas donnée toute le temps une valeur de 0)
DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE = None
# Nom du champ qui contient le chainage de fin 
DEFAULT_NOM_CHAMP_FIN_CHAINAGE ='val_longr_sous_route'


"""
    Class qui défini un objet RTSS.
    Elle permet ainsi de regrouper les méthodes pouvant être associer au RTSS (géocodage)
"""
class featRTSS:
    __slots__ = ("num_rts", "chainage_f", "geometry", "chainage_d")
    
    """
        Méthode d'initialitation de la class. Le RTSS et chainage de fin peuvent être formater, mais sont stockée
        non formater. Le chainage de début est assumé comme étant 0
        
        Entrée:
            - num_rts (str) = Le numéro de RTSS
            - chainage_f (real/str) = Le chainage de fin du RTSS, sois sa longueur en chainage
            - geometry (QgsGeometry) = La geometrie du RTSS
            - chainage_d (real/str) = Le chainage de début du RTSS, par défault toujours 0
    """
    def __init__ (self, num_rts, chainage_f, geometry, chainage_d=0):
        # Initialiser les informations du RTSS
        self.num_rts = verifyFormatRTSS(num_rts)
        self.chainage_f = verifyFormatChainage(chainage_f)
        self.geometry = geometry
        
        self.chainage_d = verifyFormatChainage(chainage_d)
        if self.chainage_d is None: self.chainage_d = 0
        
    @classmethod
    def fromFeature(cls, feat, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE):
        if isinstance(feat, QgsFeature):
            if chainage_d is None: chainage_d = 0
            else: chainage_d = feat[chainage_d]
            return cls(feat[nom_champ_rtss], feat[nom_champ_long], feat.geometry(), chainage_d=chainage_d)
        else: return cls(None, None, None)
    
    def __str__ (self):
        return f"{self.num_rts} ({self.chainage_d}, {self.chainage_f})"
    
    def __repr__ (self):
        return f"featRTSS {self.num_rts} ({self.chainage_d}, {self.chainage_f})"
    
    """ Méthode qui renvoie le numéro du RTSS. Peut être formater ou non """
    def getRTSS(self, formater=False):
        if formater: return formaterRTSS(self.num_rts)
        else: return self.num_rts
    
    """ Méthode qui renvoie le numéro de la route """
    def getRoute(self, as_int=False):
        if as_int: return int(self.num_rts[:5])
        else: return self.num_rts[:5]
    
    """ Méthode qui renvoie le numéro de troncon du RTSS """
    def getTroncon(self, as_int=False):
        if as_int: return int(self.num_rts[5:7])
        else: return self.num_rts[5:7]
        
    """ Méthode qui renvoie le numéro de section du RTSS """
    def getSection(self, as_int=False):
        if as_int: return int(self.num_rts[7:10])
        else: return self.num_rts[7:10]
        
    """ Méthode qui renvoie la sous-section du RTSS """
    def getSousSection(self):
        return self.num_rts[10:]
    
    """ Méthode qui renvoie la géometrie du RTSS """
    def getGeometry(self):
        return self.geometry
    
    """ Méthode qui renvoie le chainage de fin du RTSS, sois sa longueur en chainage. Peut être formater ou non """
    def getChainageFin(self, formater=False):
        if formater: return formaterChainage(self.chainage_f)
        else: return self.chainage_f
        
    """ Méthode qui renvoie le chainage de début du RTSS. Peut être formater ou non """
    def getChainageDebut(self, formater=False):
        if formater: return formaterChainage(self.chainage_d)
        else: return self.chainage_d
        
    """ 
        Méthode qui renvoie le chainage en entrée sur RTSS. 
        Elle s'asure que le chainage ne sois pas plus petit ou plus grand que les chainages du RTSS
    """
    def getChainageOnRTSS (self, chainage):
        if chainage < self.chainage_d: return self.chainage_d
        elif chainage > self.chainage_f: return self.chainage_f
        else: return chainage
    
    """
        Méthode qui permet de calculer une distance trace d'un point par rapport au RTSS.
        La distance du point par rapport au RTSS (positif = droite / négatif = gauche)
        
        Entrée:
            - point (QgsPointXY) = Le point à trouver la distance du RTSS
        
        Sortie:
            - dist (float) = La distance du point par rapport au RTSS (positif = droite / négatif = gauche)
    """
    def getDistanceFromPoint(self, point):
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
        # Calculer la distance et appliquer le coté (1=droit ; -1=gauche)
        dist = self.geometry.distance(verifyFormatPoint(point)) * side
        # Retourner la distance
        return dist
        
    """ 
        Méthode qui permet d'associer un chainage le long du RTSS à partir d'un point. Le point peut être sur la 
        la ligne ou avoir un offset. 
        
        Entrée:
            - point (QgsGeometry/QgsPointXY) = Le point à associer un chainage
            - formater (bool) = Indicateur pour formater le résultat du chainage
        
        Sortie:
            - chainage(real/str) = Le chainage sur le RTSS le plus proche du point. 
    """
    def getChainageFromPoint(self, point, formater=False):
        # Assurer que le point est une geometrie
        point = verifyFormatPoint(point)
        # Longueur le long de la ligne jusqu'au point le plus proche du point spécifié
        long = self.geometry.lineLocatePoint(point)
        # Chainage corriger correspondant à la longueur trouvé
        chainage = self.getChainageFromLong(long)
        
        # Formater si c'est spécifié
        if formater: chainage = formaterChainage(chainage)
        # Retourner le chainage
        return chainage
    
    def getPoint(self, point):
        return self.getPointFromChainage(point.getChainage(), point.getOffset())
        
        
    """
        Méthode qui permet de géocoder un point avec un chainage et un offset sur le RTSS.
        Le offset de la ligne par rapport au RTSS peut être positif pour un offset à droite dans le sense
        de numérisation de la ligne ou négatif pour être à gauche.
        
        Entrée:
            - chainage (real/str) = Le chainage du point à géocoder. Peut être formater ex: (2+252 ou 2252)
            - offset (real) = Le offset du point par rapport au RTSS (positif = droite / négatif = gauche)
    """
    def getPointFromChainage(self, chainage, offset=0):
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
            """ 
                Les delta X et delta Y sont de base calculer pour le cadrant Nord-Est avec l'angle du RTSS.
                Cependant, les delta reste les mêmes sauf pour le signe peut importe le cadrant
                si l'angle est (90, 180 ou 270) de plus. Le offset représente l'angle de la ligne + 90.
                Donc on applique les deltas pour le cadrant Sud-Est.
            """
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
    
    """
        Méthode qui permet de géocoder une ligne à partir d'un chainage de début et de fin.
        La ligne peut être parralel ou non et avoir un offset avec le RTSS. Si seulement un offset est définie ou
        que les deux offset sont pareil, la ligne vas être parallel au RTSS. Si deux offset sont défini,
        La difference entre les deux offset vas être répartie sur la longeur de la ligne. 
        De plus, si les deux chainage sont identique, la ligne va être perpendiculaire au RTSS.
        La ligne peut-être géocoder dans le sense contraire du chainage.
        
        Entrée:
            - chainage_d (real/str) = Le chainage de début. Peut être formater ex: (2+252 ou 2252)
            - chainage_f (real/str) = Le chainage de fin. Peut être formater ex: (2+252 ou 2252)
            - offset_d (real) = Le offset de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f (real) = Le offset de fin de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - iterpolate_middle (bool) = L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
            - reverse_geom (bool) = L'indicateur pour avoir une line dont la géomtrie est inverse au sense du chainage 
        Sortie:
            - line_geom (QgsGeometry) = La géometrie linéaire géocoder
    """
    def getLineFromChainage(self, chainage_d, chainage_f, offset_d=0, offset_f=None, iterpolate_middle=True, reverse_geom=False):
            
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
                    if current_chainage >= chainage_f: 
                        break
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
    
    
    """
        Méthode qui permet de géocoder un polygone à partir de quatre combinaisons de chainage/offset
        Le polygone est construit avec deux lignes géocoder. Donc les deux premières combinaisons représente
        une premières ligne géocodé et les deux autre combinaisons représente la deuxième ligne géocoder dans l'autre dirrection.
        
        Entrée:
            - chainage_d1 (real/str) = Le chainage de début de la première ligne. Peut être formater ex: (2+252 ou 2252)
            - chainage_f1 (real/str) = Le chainage de fin de la première ligne. Peut être formater ex: (2+252 ou 2252)
            - offset_d1 (real) = Le offset de la première ligne de début par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f1 (real) = Le offset de la première ligne de fin par rapport au RTSS (positif = droite / négatif = gauche)
            - chainage_d2 (real/str) = Le chainage de début de la deuxième ligne. Peut être formater ex: (2+252 ou 2252)
            - chainage_f2 (real/str) = Le chainage de fin de la deuxième ligne. Peut être formater ex: (2+252 ou 2252)
            - offset_d2 (real) = Le offset de la deuxième ligne de début par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f2 (real) = Le offset de la deuxième ligne de fin par rapport au RTSS (positif = droite / négatif = gauche)
            - iterpolate_middle (bool) = L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
        Sortie:
            - geom (QgsGeometry) = La géometrie polygonal géocoder
    """
    def getPolygonFromChainage(self, chainage_d1, chainage_f1, offset_d1, offset_d2, chainage_d2=None, chainage_f2=None, offset_f1=None, offset_f2=None, iterpolate_middle=True):
        pts = [self.setPointRTSS(chainage_d1, offset_d1), self.setPointRTSS(chainage_f1, offset_f1), self.setPointRTSS(chainage_d2, offset_d2), self.setPointRTSS(chainage_f2, offset_f2)]
        # Liste des points composant le polygone
        list_points = [point for point in pts if point]
        return self.getPolygon(list_points, iterpolate_middle=iterpolate_middle)
    
    """ 
        Méthode qui retourne le chainage correspondant à la longueur demandé le long du RTSS
        Chaînage --> Distance géometrique
        
        Entrée:
            - chainage (float/int) = Le chainage à convertir en longueur géometrique 
        
        Sortie:
            - long_corriger (float/int) = La longueur géometrique correspondant au chainage en entrée
    """
    def getLongFromChainage (self, chainage):
        # Longueur du RTSS
        long_rtss = self.geometry.length()
        # Chainage 
        chainage = verifyFormatChainage(chainage)
        
        # Chaînage --> Distance géometrique
        if chainage >= self.chainage_f:
            # Retourner la longueur geometrique max si le chainage est plus grande que le chainage de fin 
            long_corriger = long_rtss
        
        # Si le chainage est plus petit que le chainage de début du RTSS, retourné le chainage de début du RTSS
        elif chainage <= self.chainage_d:
            long_corriger = self.chainage_d
        else:
            # Sinon corriger le chainage pour obtenir la longueur géometrique
            long_corriger = (chainage * long_rtss)/self.chainage_f
            
        # Retourner la longueur géometrique
        return long_corriger
    
    """ 
        Méthode qui retourne le chainage correspondant à la longueur demandé le long du RTSS
        Distance géometrique --> Chaînage
        
        Entrée:
            - longueur (float/int) = La longueur géometrique à corriger le long du RTSS
        
        Sortie:
            - chainage_corriger (float/int) = Le chainage correspondant à la longueur en entrée
    """
    def getChainageFromLong (self, longueur):
        # Longueur du RTSS
        long_rtss = self.geometry.length()
        
        # Distance géometrique --> Chaînage
        if longueur >= long_rtss:
            # Retourner le chainage de fin si la longueur est plus grande que la longueur du RTSS
            chainage_corriger = self.chainage_f
            
        # Si la longueur est plus petit que le chainage de début du RTSS retourner le chainage de début du RTSS
        elif longueur <= self.chainage_d:
            chainage_corriger = self.chainage_d 
        else:
            chainage_corriger = (longueur * self.chainage_f)/ long_rtss
            
        # Retourner la longueur corrigée
        return chainage_corriger

    """
        Méthode qui crée une ligne perpendiculaire au RTSS. Par défault le transect est de gauche => droite, mais peut
        être inversé droite => gauche.

        Entrée:
            - chainage (real/str) = Le chainage du transect. Peut être formater ex: (2+252 ou 2252)
            - dist_d (real) = La longueur du transect à droite.
            - dist_g (real) = La longueur du transect à gauche.
            - inverse (bool) = Indicateur du sense du transect 
                                True: droite => gauche
                                False: gauche => droite
        
        Sortie:
            - transect (QgsGeometry) = La géometrie linéaire du transect
    """
    def getTransect (self, chainage, dist_d, dist_g, inverse=False):
        # Point à droite du RTSS
        pt_droit = self.getPointFromChainage(chainage, dist_d)
        # Point à gauche du RTSS
        pt_gauche = self.getPointFromChainage(chainage, dist_g*-1)
        
        # Inverser les points si spécifié
        if inverse: pt_droit, pt_gauche = pt_gauche, pt_droit
        # Créer une ligne entre les deux points
        transect = QgsGeometry().fromPolylineXY([pt_gauche.asPoint(), pt_droit.asPoint()])

        return transect
    
    def getAngleAtChainage(self, chainage):
        # Vérifier chainage 
        chainage = verifyFormatChainage(chainage)
        # Longueur géometrique correspondant au chainage
        long = self.getLongFromChainage(chainage)
        
        # Angle en radian du RTSS au chainage dans le sense horraire par raport au Nord
        angle = self.geometry.interpolateAngle(long)
        # Angle en degrees
        degres_angle = math.degrees(angle)
        
        return degres_angle
    
    def interpolateOffsetAtChainage(self, chainage, chainage_d, chainage_f, offset_d, offset_f):
        if chainage_d == chainage_f: return None
        if offset_d == offset_f: return offset_d
        
        long_d = self.getLongFromChainage(chainage_d)
        long_f = self.getLongFromChainage(chainage_f)
        long = self.getLongFromChainage(chainage)
        # Différence du offset
        offset_diff = offset_f - offset_d
        # Longueur de la nouvelle ligne
        longueur_ligne = long_f - long_d
        
        return (((long-long_d) * offset_diff)/longueur_ligne) + offset_d
    
    def isChainageOnRTSS(self, chainage):
        return chainage >= self.chainage_d and chainage <= self.chainage_f
    
    def setPointRTSS(self, chainage, offset=0):
        if chainage is None or offset is None: return None
        return PointRTSS(self.getRTSS(), self.getChainageOnRTSS(chainage), offset)



"""
    Une class qui permet d'éffectuer des oppérations de géocodage à partir d'une couche de RTSS.
"""
class geocodage:
    
    """ 
        Initialisation de la class de géocodage avec une couche contenant les RTSS à utiliser.
        La class conserve en mémoire seulement les geometries et les informations des deux champs.
        L'instance du QgsVectorLayer peut donc être supprimé sans problème. 
        
        * Les valeurs par défault sont les noms des champs de la couche BGR - RTS du WFS 
        Entrée:
            - rtss_features(QgsFeaturesIterator) = La couche des RTSS
            - crs (QgsCoordinateReferenceSystem) = Le sytème de coordonnée de la couche
            - nom_champ_rtss (str) = Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str) = Le nom du champ de la couche contenant le chainage de fin du RTSS
            - nom_champ_chainage_d (str) = Le nom du champ de la couche contenant le chainage de début du RTSS
            - precision (int) = Précison du chainage, Nombre de chiffre après la virgule
            - interpolate_on_rtss (bool) = L'indicateur pour interpoler les valeurs le long du rtss entre les deux points
    """
    def __init__ (self, rtss_features, crs, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, precision=0, interpolate_on_rtss=True):
        
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
        # Indicateur de l'absence de RTTS valide
        self.is_empty = True
        # Référence du system de coordonnée
        self.setCRS(crs)
        
        # Créer la référence des RTSS
        self.updateReferenceDesRTSS(rtss_features)
    
    """ Constructeur avec la couche QgsVectorLayer des RTSS """
    @classmethod
    def fromLayer(cls, layer, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, precision=0, interpolate_on_rtss=True):
        if isinstance(layer, QgsVectorLayer): return cls(layer.getFeatures(), layer.crs(), nom_champ_rtss, nom_champ_long, nom_champ_chainage_d, precision, interpolate_on_rtss)
        else: return cls(None, None)
    
    """ Constructeur avec le nom de la couche des RTSS dans le projet courrant """
    @classmethod
    def fromProject(cls, layer_name=DEFAULT_NOM_COUCHE_RTSS, nom_champ_rtss=DEFAULT_NOM_CHAMP_RTSS, nom_champ_long=DEFAULT_NOM_CHAMP_FIN_CHAINAGE, nom_champ_chainage_d=DEFAULT_NOM_CHAMP_DEBUT_CHAINAGE, precision=0, interpolate_on_rtss=True):
        layer = validateLayer(layer_name, [nom_champ_rtss, nom_champ_long], geom_type=1)
        if layer: return cls(layer.getFeatures(), layer.crs(), nom_champ_rtss, nom_champ_long, nom_champ_chainage_d, precision, interpolate_on_rtss)
        else: return cls(None, None)
    
    def __repr__ (self):
        return f"Geocodage ({len(self.dict_rtss)} RTSS)"
        
    """ Méthode qui retourne l'indicateur le l'instantiation de la class. Retourn True tant que la class n'a pas des RTTS valide"""
    def isEmpty(self): return self.is_empty
    
    """ Méthode qui permet de créer ou de mettre à jour la référence des RTSS
        
        Entrée:
            - rtss_features(QgsFeaturesIterator) = La nouvelle couche des RTSS
            - crs (QgsCoordinateReferenceSystem) = Le système de coordonnée de la couche
            - nom_champ_rtss (str) = Le nom du champ de la couche contenant les numéros des RTSS
            - nom_champ_long (str) = Le nom du champ de la couche contenant le chainage de fin du RTSS
    """
    def updateReferenceDesRTSS(self, rtss_features, crs=None, nom_champ_rtss=None, nom_champ_long=None, nom_champ_chainage_d=None):
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
        self.is_empty = self.dict_rtss == {}
            
    """ Retourne le EPSG courrant de l'object """ 
    def getEpsg(self):
        if isinstance(self.crs, QgsCoordinateReferenceSystem): return self.crs.authid()
        else: return None
    
    """ Retourne le CRS courrant de l'object """
    def getCrs(self): return self.crs
    
    def getPointOnRTSS(self, point, formater_rtss=False, formater_chainage=False):
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
    
    """ 
        Fonction qui retourne l'instance de la class featRTSS pour un RTSS.
        Retourne une valeur vide si le RTSS n'existe pas
        
        Entrée:
            - rtss(str) = Le numéro de RTSS formater ou non (00010-01-235-000D ou 0001001235000D)
            
        Sortie:
            - rtss_geom (featRTSS) = La class featRTSS du RTSS
    """ 
    def getRTSS(self, rtss, rtss_complet=True):
        rtss = verifyFormatRTSS(rtss)
        # Vérifier si le RTSS existe dans le dictionnaire
        if rtss in self.dict_rtss and rtss_complet:
            # Si le RTSS existe, retourner la classe featRTSS
            return self.dict_rtss[rtss]
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
        # Liste de toutes les RTSS
        list_rtss = list(self.dict_rtss.keys())
        
        # Formater la liste si nécéssaire
        if formater: list_rtss = [formaterRTSS(rtss) for rtss in list_rtss]
        # Trier la liste si nécéssaire
        if sorted: list_rtss.sort()
        # Retourner la liste
        return list_rtss
            
    """
        Méthode qui renvoie une géometrie à partir d'un RTSS/chainage.
        Elle peut géocoder des geometries ponctuelle ou linéaire.
        Les géometries linéaire peuvent avoir un offset. Si seulement un offset est définie ou
        que les deux offset sont pareille, la ligne vas être parallel au RTSS. Si deux offset sont défini,
        La difference entre les deux offset vas être répartie sur la longeur de la ligne. 
        
        Entrée:
            - rtss (str) = Le numéro du RTSS. Peut être formater ex: (0001002155000D ou 00010-02-155-000D)
            - chainage (real/str) = Le chainage de début. Peut être formater ex: (2+252 ou 2252)
            - chainage_f (real/str) = Le chainage de fin. Peut être formater ex: (2+252 ou 2252)
            - offset (real) = Le offset de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - offset_f (real) = Le offset de fin de la ligne par rapport au RTSS (positif = droite / négatif = gauche)
            - reverse (bool) = Inverser la géometrie
        
        Sortie:
            - geom (QgsGeometry) = La géometrie géocoder (ponctuelle ou linéaire)
    """
    def geocoder(self, rtss, chainage, chainage_f=None, offset=0, offset_f=None, chainage_d2=None, chainage_f2=None, offset_d2=None, offset_f2=None, reverse=False):
        # S'assurer que le RTSS est dans la bonne manière
        rtss = verifyFormatRTSS(rtss)
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
                    iterpolate_middle=iterpolate_middle, reverse_geom=reverse_geom).asPolyline()
                list_polygon_points += ligne[:-1]
            
        # Retourner la géometries géocoder
        return geom
    
    """
        Méthode qui associe un RTSS/chainage à une géometrie ponctuelle ou linéaire. Un RTSS peux être spécifié
        s'il est connue. Sinon le RTSS le plus proche est selectionnée. Pour selectionnée le RTSS le plus proche,
        d'un entités linéaire, c'est la sum des distance avec le point de début et de fin.
        
        Entrée:
            - geometry (QgsGeometry) = La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            - rtss(str) = Le numéro du RTSS. Peut être formater ex: (0001002155000D ou 00010-02-155-000D)
            - formater_rtss (bool) = Idicateur pour formater le résultat du RTSS
            - formater_chainage (bool) = Idicateur pour formater les résultat des chainage
        
        Sortie:
            - Dictinaire avec le numéro du RTSS et le chainage de début et de fin. (Pour un point, les deux chainage sont identique)
                ex: {'rtss': 0001002155000D,
                    'chainage_d': 1533,
                    'chainage_f': 2482}
    """
    def geocoderInverse(self, geometry, rtss=None, formater_rtss=False, formater_chainage=False):
        # Vérifier que le RTSS est dans la bonne manière
        if rtss: rtss = verifyFormatRTSS(rtss)
            
        # Vérifier si un RTSS est défini et est dans la dictionnaire de référence
        if rtss in self.dict_rtss:
            # Si oui aller chercher directement le featRTSS
            feat_rtss = self.dict_rtss[rtss]
        else:
            # Sinon appeller la fonction pour avoir le RTSS le plus proche de la géometrie
            feat_rtss = self.nearestRTSS(geometry)[0]['rtss']
        
        # Liste des chainages les plus proche de chacun des vertex de la ligne en entrée 
        list_chainage = [feat_rtss.getChainageFromPoint(QgsPointXY(vertex.x(), vertex.y())) for vertex in geometry.vertices()]
        
        # Formater les chainage si spécifié
        if formater_chainage:
            chainage_min = formaterChainage(min(list_chainage), self.precision)
            chainage_max = formaterChainage(max(list_chainage), self.precision)
        else:
            chainage_min = round(min(list_chainage), self.precision)
            chainage_max = round(max(list_chainage), self.precision)
        
        # Dictionnaire avec les résultat des RTSS, chainage_d et chainage_f
        dict_res = {'rtss': feat_rtss.getRTSS(formater=formater_rtss), 'chainage_d': chainage_min, 'chainage_f': chainage_max}
        
        # Retourne le dictionnaire résultat
        return dict_res
    
    """
        Méthode qui permet d'associer un RTSS/chainage à une géometrie ponctuelle. 
        Un RTSS peux être spécifié s'il est connue. Sinon le RTSS le plus proche est selectionnée.
    """
    def geocoderInversePoint(self, geom_point, rtss=None, get_offset=False, concatenante=False, formater_rtss=False, formater_chainage=False):
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
        list_values = []
        for vertex in geom_line.vertices():
            # Trouver la valeur RTSS / chainage du vertex
            value = self.geocoderInversePoint(
                QgsGeometry.fromPointXY(QgsPointXY(vertex.x(), vertex.y())),
                rtss=rtss,
                get_offset=get_offset,
                concatenante=concatenante,
                formater_rtss=formater_rtss,
                formater_chainage=formater_chainage)
            list_values.append(value)
        
        # Dictionnaire avec les résultat des RTSS, chainage_d et chainage_f
        return list_values
        
        
    
    """
        Méthode pour determiner les featRTSS, dans la référence des RTSS, les plus proche d'une geometrie.
        La géometrie peut être ponctuelle ou linéaire. Pour identifier le RTSS le plus proche d'une ligne,
        la moyenne des distance avec le point de début et de fin est utiliser. Cela permet de ne pas retourner 
        un RTSS qui croise une ligne à une place alors que la ligne est clairement parallel à un autre RTSS.
        
        Entrée:
            - geometry (QgsGeometry) = La géometrie à trouvé un RTSS/chainage (ponctuelle ou linéaire)
            
        Sortie :
            - list_nearest_rtss(liste) = Liste ordonnée avec les featRTSS et dist des rtss les plus proche
                Ex:[{'rtss':featRTSS(), 'distance':10}, {'rtss':featRTSS(), 'distance':15}]
    """
    def nearestRTSS(self, geometry, nbr=1, dist_max=0):
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
        # Instance de la class featRTSS contenant toute les informations du RTSS
        feat_rtss = self.getRTSS(rtss)
        # Geometry vide
        angle = None
        # Vérifier que le RTSS est dans la référence des RTSS
        if feat_rtss:
            angle = feat_rtss.getAngleAtChainage(chainage)
        
        return angle
    
    """
        Méthode qui permet de définir le système de coordonnée des geometries utilisé. 
        Il doit être un instance de la class QgsCoordinateReferenceSystem de QGIS et avoir une projection en mètre
        
        Entrée:
            - crs (QgsCoordinateReferenceSystem) = Le système de coordonnée des géometries des RTSS
    """
    def setCRS(self, crs):
        self.crs = None
        if isinstance(crs, QgsCoordinateReferenceSystem):
            self.crs = crs
            self.epsg = self.crs.authid()
            # La couche des RTSS doit être projeté dans une projection en mètre
            if self.crs.mapUnits() != 0:
                raise Exception("L'unité de la couche des RTSS doit être en mètre.")
    
    """
        Méthode pour définir la précision des chainages à retourner.
        
        Entrée:
            - precision (int) = La valeur pour l'arrondi (entier positif = nbr décimal / entier négatif = la dizaine)
    """
    def setPrecision(self, precision):
        if isinstance(precision, int): 
            self.precision = precision
            return True
        return False
    
    """
        Méthode pour définir l'indicateur d'interpolation. 
    """
    def setInterpolation(self, interpolate_on_rtss):
        self.interpolate_on_rtss = interpolate_on_rtss

    """ 
    Polystrip plugin:
        begin                : 2017-07-29
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com 
    following code mostly taken from
    https://gis.stackexchange.com/questions/173127/generating-equal-sized-polygons-along-line-with-pyqgis

    """
    def getAtlasPages(self, start, width, height, end=None, overlap=20, start_offset=10):
        rtss = start.getRTSS()
        # Instance de la class featRTSS contenant toute les informations du RTSS
        feat_rtss = self.getRTSS(rtss)
        # Vérifier que le RTSS est dans la référence des RTSS
        if not feat_rtss: return None
        
        # Create the atlas pages layer
        layer_pages = QgsVectorLayer(f"Polygon?crs={str(self.getEpsg())}", "Atlas_pages", "memory")
        attributes = [
            QgsField("rtss", QVariant.String),
            QgsField("chainage_d", QVariant.Int),
            QgsField("chainage_f", QVariant.Int),
            QgsField("angle", QVariant.Double),
            QgsField("atl_ang", QVariant.Double)]
        pages_provider = layer_pages.dataProvider()
        pages_provider.addAttributes(attributes)
        layer_pages.updateFields()
        
        if end: geometrie = feat_rtss.getLineFromChainage(start.getChainage(), end.getChainage())
        else: geometrie = feat_rtss.getLineFromChainage(start.getChainage(), feat_rtss.getChainageFin())
        
        extended_geom = QgsGeometry.extendLine(geometrie, (start_offset/100) * width, overlap)
        
        curs = 0
        geom_length = geometrie.length() 
        step = 1.0 / (geom_length / width)
        stepnudge = (1.0 - (overlap/100)) * step
        page_features = []
        while curs <= 1:
            # Get the first point for the polygon
            start_point = extended_geom.interpolate(curs * geom_length)
            # interpolate returns no geometry when > 1
            forward = curs + step
            if forward > 1: forward = 1
            # Get the last point for the polygon
            end_point = extended_geom.interpolate(forward * geom_length)
            
            # Define the page geometrie
            page_geom = QgsGeometry().fromWkt('POLYGON((0 0, 0 {height},{width} {height}, {width} 0, 0 0))'.format(
                height=height, width=width))
            page_geom.translate(0, -height/2)
            azimuth = start_point.asPoint().azimuth(end_point.asPoint())
            currangle = (azimuth+270) % 360
            page_geom.rotate(currangle, QgsPointXY(0, 0))
            page_geom.translate(start_point.asPoint().x(), start_point.asPoint().y())
            page_geom.asPolygon()
            
            # Create new page feature
            feat = QgsFeature()
            feat.setAttributes([
                rtss,
                feat_rtss.getChainageFromPoint(start_point),
                feat_rtss.getChainageFromPoint(end_point),
                currangle,
                360-currangle])
            feat.setGeometry(page_geom)
            page_features.append(feat)
            
            # Advance current position
            curs = curs + stepnudge
        
        pages_provider.addFeatures(page_features)
        
        return layer_pages



class PointRTSS:

    def __init__ (self, rtss, chainage, offset=0):
        self.setRTSS(rtss)
        self.setChainage(chainage)
        self.setOffset(offset)
        
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