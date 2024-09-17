from qgis.core import *
from qgis.utils import plugins

GROUP_NAME = 'Géocodage MTQ'

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def get_rtss(geom_point, feature, parent):
    """
    Permet de retourner le RTSS le plus proche d'une geometry ponctuel<br>
    
    <ul>
      <li>geom_point(QgsGeometry) -> La géometrie du point à utiliser</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>get_rtss($geometry) -> 0002001020000D</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: val = geocode.geocoderInversePoint(geom_point).getRTSS().value()
    except: val = ""
    return val


@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def get_rtss_formater(geom_point, feature, parent):
    """
    Permet de retourner le RTSS formater le plus proche d'une geometry ponctuel<br>
    
    <ul>
      <li>geom_point(QgsGeometry) -> La géometrie du point à utiliser</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>get_rtss_formater($geometry) -> 00020-01-020-000D</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: val = geocode.geocoderInversePoint(geom_point).getRTSS().value(True)
    except: val = ""
    return val
    
@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def get_chainage(geom_point, feature, parent):
    """
    Permet de retourner le chainage le plus proche d'une geometry ponctuel<br>
    
    <ul>
      <li>geom_point(QgsGeometry) -> La géometrie du point à utiliser</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>get_chainage($geometry) -> 1030</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: val = geocode.geocoderInversePoint(geom_point).getChainage().value()
    except: val = ""
    return val

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def get_chainage_formater(geom_point, feature, parent):
    """
    Permet de retourner le chainage formater le plus proche d'une geometry ponctuel<br>
    
    <ul>
      <li>geom_point(QgsGeometry) -> La géometrie du point à utiliser</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>get_chainage_formater($geometry) -> 1+030</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: val = geocode.geocoderInversePoint(geom_point).getChainage().value(True)
    except: val = ""
    return val
    
@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def get_distance_to_rtss(geom_point, feature, parent):
    """
    Permet de retourner la distance du RTSS le plus proche d'une geometry ponctuel<br>
    
    <ul>
      <li>geom_point(QgsGeometry) -> La géometrie du point à utiliser</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>get_distance_to_rtss($geometry) -> 24.322</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: val = geocode.geocoderInversePoint(geom_point).getOffset()
    except: val = ""
    return val

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def geocoder_point(rtss, chainage, offset, feature, parent):
    """
    Permet de retourner une geometrie représentant un point au RTSS/chainage/offset<br>
    * Les rtss et chainage peuvent être formater.<br>
    <ul>
      <li>rtss(str) -> Le rtss du point à définir</li>
    </ul>
    <ul>
      <li>chainage(str/nombre) -> Le chainage sur le rtss pour le point à définir</li>
    </ul>
    <ul>
      <li>offset(nombre) -> Le offset du point. Droite(+) Gauche(-) </li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>geocoder_point('0013901020000C', '2+034', 0) -> QgsGeometry</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: 
        point_rtss = geocode.createPoint(rtss, chainage, offset)
        geom_point = geocode.geocoderPoint(point_rtss)
    except: geom_point = QgsGeometry()
    return geom_point

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def geocoder_line(rtss, list_chainage, list_offset, feature, parent):
    """
    Permet de retourner une geometrie représentant une ligne sur le RTSS pour les chainage et offset<br>
    * Les rtss et chainage peuvent être formater.<br>
    <ul>
      <li>rtss(str) -> Le rtss de la ligne à définir</li>
    </ul>
    <ul>
      <li>list_chainage (list of [str/nombre]) -> Les chainages sur le rtss pour la ligne à définir</li>
    </ul>
    <ul>
      <li>list_offset (list of [nombre]) -> Les offsets de la ligne. Droite(+) Gauche(-) </li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>geocoder_line('0013901020000C', array('2+034', '3+000), array(0, 0)) -> QgsGeometry</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: 
        line_rtss = geocode.createLine(rtss, list_chainage, list_offset)
        geom_line = geocode.geocoderLine(line_rtss)
    except: geom_line = QgsGeometry()
    return geom_line

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def geocoder_polygon(rtss, list_chainage, list_offset, feature, parent):
    """
    Permet de retourner une geometrie représentant un polygone sur le RTSS pour les chainage et offset<br>
    * Les rtss et chainage peuvent être formater.<br>
    <ul>
      <li>rtss(str) -> Le rtss du polygon à définir</li>
    </ul>
    <ul>
      <li>list_chainage (list of [str/nombre]) -> Les chainages sur le rtss pour le polygon à définir</li>
    </ul>
    <ul>
      <li>list_offset (list of [nombre]) -> Les offsets du polygon. Droite(+) Gauche(-) </li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>geocoder_polygon('0013901020000C', array('2+034', '3+000', '3+000', '2+034'), array(0, 0, 10, 10)) -> QgsGeometry</li>
    </ul>
    """
    geocode = plugins['outils_MTQ_chainage'].getModuleGeocodage()
    try: 
        polygon_rtss = geocode.createPolygon(rtss, list_chainage, list_offset)
        geom_polygon = geocode.geocoderPolygon(polygon_rtss)
    except: geom_polygon = QgsGeometry()
    return geom_polygon
