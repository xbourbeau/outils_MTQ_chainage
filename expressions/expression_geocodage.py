from itertools import chain
from qgis.core import *
from qgis.utils import plugins

from ..modules.PluginParametres import PluginParametres

GROUP_NAME = PluginParametres().getValue("expression_group_name")

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def formater_rtss(rtss, feature, parent):
  """
  Permet de retourner un RTSS ou un RTS formaté avec les tirets<br>
  
  <ul>
    <li>rtss(str) -> Le numéro du RTSS à formater</li>
  </ul>
  <h2>Example usage:</h2>
  <ul>
    <li>formater_rtss('0002001020000D') -> 00020-01-020-000D</li>
    <li>formater_rtss('0002001020') -> 00020-01-020</li>
  </ul>
  """
  sections = [sect for sect in [rtss[:5], rtss[5:7], rtss[7:10], rtss[10:]] if sect]
  # Retourner le RTSS formater
  return "-".join(sections)

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def formater_chainage(chainage, feature, parent):
    """
    Permet de retourner un chainage formaté avec le signe de "+" qui sépare les miller<br>
    
    <ul>
      <li>chainage(str ou nombre) -> La valeur du chainage à formater</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>formater_chainage('473') -> 0+473</li>
      <li>formater_chainage(1473.48) -> 1+473,48</li>
    </ul>
    """
    try:
        if isinstance(chainage, str):
            if "," in chainage: chainage = chainage.replace(",", ".")
            if "." in chainage: chainage = float(chainage)
            else: chainage = int(chainage)
    except: raise Exception("La valeur text ne peux pas etres converti en chiffre")
    
    if isinstance(chainage, float): 
        # Déterminer la précision si elle n'est pas déterminé
        precision = [round(chainage, i) == round(chainage,10) for i in range(10)]
        try: precision = precision.index(True)
        except: precision = 10
    elif isinstance(chainage, int): precision = 0
    else: raise Exception("La valeur doit etre un text ou un chiffre")

    # Determiner si le format est entier ou réel
    if precision <= 0:
        # Calculer le chainage arrondie selon la précision définie
        chainage = int(round(chainage, precision))
        # Format à appliquer pour un nombre entier
        number_format = '{:03}'
    # Format à appliquer pour un nombre réel avec la précision définie
    else: number_format = '{:0%i.%if}' % (4 + precision, precision)
    # Déterminer les milliers
    millier = int(chainage / 1000)
    # Retourner le nombre selon le formatage définie 
    return str(millier) + "+" + number_format.format(chainage - (millier*1000)) 

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def deformater_rtss(rtss, feature, parent):
  """
  Permet de retourner un RTSS ou un RTS à partir d'un RTSS ou un RTS formaté<br>
  
  <ul>
    <li>rtss(str) -> Le numéro du RTSS à déformater</li>
  </ul>
  <h2>Example usage:</h2>
  <ul>
    <li>deformater_rtss('00020-01-020-000D') -> 0002001020000D</li>
    <li>deformater_rtss('00020-01-020') -> 0002001020</li>
  </ul>
  """
  try: return rtss.replace("-", "")
  except: raise Exception("Impossible de retirer le tiret du RTSS")

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def deformater_chainage(chainage, feature, parent):
    """
    Permet de retourner un chainage non formaté à partir d'un chainage formaté<br>
    
    <ul>
      <li>chainage(str) -> La valeur du chainage à déformater</li>
    </ul>
    <h2>Example usage:</h2>
    <ul>
      <li>deformater_chainage(0+473) -> 473</li>
      <li>deformater_chainage(1+473,48) -> 1473.48</li>
    </ul>
    """
    try:
        chainage = str(chainage)
        # Déterminer la précision si elle n'est pas déterminé
        if ',' in chainage: chainage = chainage.replace(",", ".")
        if '.' in chainage: precision = len(chainage[chainage.find('.')+1:])
        else: precision = 0

        if '+' not in chainage: 
            return int(chainage) if precision <= 0 else float(chainage)  
        # Séparer les milliers et les centaines par le "+"
        millier, centaine = chainage.split('+')
        # Convertir les milliers et les centaines en nombre
        val_convertie = int(millier) * 1000 + float(centaine)
        # Arrondir la valeur selon la précision définie
        val_convertie = round(val_convertie, precision)
        # Convertir en nombre entier si la précision est de 0 ou moins
        if precision <= 0: val_convertie = int(val_convertie)
        
        # Retourner la valeur formatée
        return val_convertie
    except: raise Exception("Impossible de convertir le chainage en chiffre")

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
