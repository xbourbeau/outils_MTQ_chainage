from itertools import chain

from ast import literal_eval
from matplotlib.transforms import offset_copy
from mtq import search
from qgis.core import *
from qgis.utils import plugins

from ..mtq.core import SIGO, PlaniActif
from ..modules.PluginParametres import PluginParametres

GROUP_NAME = PluginParametres().getValue("expression_group_name")

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def lien_sigo(geom:QgsGeometry, crs:QgsCoordinateReferenceSystem, feature, parent):
  """
  Permet de retourner un lien SIGO avec une vue sur un étendu d'une géometrie en entrée.<br>
  
  <ul>
    <li>geom(QgsGeometry) -> La géometry à utiliser pour l'étendue (bounding box)</li>
    <li>crs(int/str) -> Le CRS de la géometry donnée. Ex: 'EPSG:3857' ou 3857</li>
  </ul>
  <h2>Example usage:</h2>
  <ul>
    <li>lien_sigo($geometry, 3857)<br>
    Permet de retourner le lien pour ouvrir SIGO avec une vue sur la géométrie courant</li>
    <li>lien_sigo(buffer($geometry, 100), 'EPSG:3857')<br>
    Permet de retourner le lien pour ouvrir SIGO avec une vue sur la géométrie courant</li>
  </ul>
  """
  # Retourner le RTSS formater
  return SIGO().getURLFromExtent(extent=geom.boundingBox(), crs=crs)

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def lien_sigo_complet(geom:QgsGeometry, crs, max_zoom, offset, layers_wms, search, feature, parent):
  """
  Permet de retourner un lien SIGO avec une vue sur un étendu d'une géometrie en entrée.<br>
  
  <ul>
    <li>geom(QgsGeometry) -> La géometry à utiliser pour l'étendue (bounding box)</li>
    <li>crs(int/str) -> Le CRS de la géometry donnée. Ex: 'EPSG:3857' ou 3857</li>
    <li>max_zoom(int) -> Maximum zoom level to consider (default 19)</li>
    <li>offset(int) -> Ajouter des niveau de zoom a celui calculer</li>
    <li>layers_wms(str) -> Text évauluer en dictionnaire qui contient les URL et les noms des couche à ajouter. Defaults to {}</li>
    <li>search(str) -> n argument à rechercher dans la barre de recherche SIGO</li>
  </ul>
  <h2>Example usage:</h2>
  <ul>
    <li>lien_sigo_complet(<br>
	    buffer(@geometry, 100),<br>
	    'EPSG:3857',<br>
	    19,<br>
	    2,<br>
      '{"https://ws.mapserver.mtq.min.intra/donnee_systeme":["iit_cond_ligne_permn"]}',<br>
	    '')
    </li>
  </ul>
  """
  # Retourner le RTSS formater
  return SIGO().getURLFromExtent(
    extent=geom.boundingBox(),
    max_zoom=max_zoom,
    offset=offset,
    layers_wms=literal_eval(layers_wms),
    search=search,
    crs=crs)

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def lien_planiactif(geom:QgsGeometry, crs:QgsCoordinateReferenceSystem, feature, parent):
  """
  Permet de retourner un lien PlaniActif avec une vue sur un étendu d'une géometrie en entrée.<br>
  
  <ul>
    <li>geom(QgsGeometry) -> La géometry à utiliser pour l'étendue (bounding box)</li>
    <li>crs(int/str) -> Le CRS de la géometry donnée. Ex: 'EPSG:3857' ou 3857</li>
  </ul>
  <h2>Example usage:</h2>
  <ul>
    <li>lien_planiactif($geometry, 3857)<br>
    Permet de retourner le lien pour ouvrir PlaniActif avec une vue sur la géométrie courant</li>
    <li>lien_planiactif(buffer($geometry, 100), 'EPSG:3857')<br>
    Permet de retourner le lien pour ouvrir PlaniActif avec une vue sur la géométrie courant</li>
  </ul>
  """
  # Retourner le RTSS formater
  return PlaniActif().getURLFromExtent(extent=geom.boundingBox(), crs=crs)

@qgsfunction(args='auto', group=GROUP_NAME, referenced_columns=[])
def lien_planiactif_complet(geom:QgsGeometry, crs, max_zoom, offset, layers_wms, search, feature, parent):
  """
  Permet de retourner un lien planiactif avec une vue sur un étendu d'une géometrie en entrée.<br>
  
  <ul>
    <li>geom(QgsGeometry) -> La géometry à utiliser pour l'étendue (bounding box)</li>
    <li>crs(int/str) -> Le CRS de la géometry donnée. Ex: 'EPSG:3857' ou 3857</li>
    <li>max_zoom(int) -> Maximum zoom level to consider (default 19)</li>
    <li>offset(int) -> Ajouter des niveau de zoom a celui calculer</li>
    <li>layers_wms(str) -> Text évauluer en dictionnaire qui contient les URL et les noms des couche à ajouter. Defaults to {}</li>
    <li>search(str) -> n argument à rechercher dans la barre de recherche planiactif</li>
  </ul>
  <h2>Example usage:</h2>
  <ul>
    <li>lien_planiactif_complet(<br>
	    buffer(@geometry, 100),<br>
	    'EPSG:3857',<br>
	    19,<br>
	    2,<br>
      '{"https://ws.mapserver.mtq.min.intra/donnee_systeme":["iit_cond_ligne_permn"]}',<br>
	    '')
    </li>
  </ul>
  """
  # Retourner le RTSS formater
  return PlaniActif().getURLFromExtent(
    extent=geom.boundingBox(),
    max_zoom=max_zoom,
    offset=offset,
    layers_wms=literal_eval(layers_wms),
    search=search,
    crs=crs)
