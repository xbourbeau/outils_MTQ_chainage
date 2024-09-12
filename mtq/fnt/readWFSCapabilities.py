import requests
from xml.etree import ElementTree as ET
try: from requests_negotiate_sspi import HttpNegotiateAuth
except: pass

def layerPossibleCRS(wfs_server:str, layer_name:str):
    """
    Permet de retourner la liste des WFS possible d'une couche WFS

    Args:
        wfs_server (str): Le lien vers le MapServer du WFS 
        layer_name (str): Nom de la couche dans le MapServer du WFS

    Returns: Liste des CRS possible ex: ['EPSG:3798', 'EPSG:3799']
    """
    wfs_server = wfs_server.split("?")[0]
    wfs_server += "?service=WFS&version=2.0.0&request=GetCapabilities"
    # Fetch the WFS capabilities document with authentication and custom CA bundle
    response = requests.get(wfs_server, auth=HttpNegotiateAuth(), verify=False)
    # Vérifier que la réponse est valide
    if response.status_code != 200: return None

    # Parse the capabilities document
    capabilities = ET.fromstring(response.content)
    # Determiner l'élément qui contient les couches
    feature_list = capabilities.findall('{http://www.opengis.net/wfs/2.0}FeatureTypeList')[0]
    # Parcourir les couche du mapserver
    for feature in feature_list.findall('{http://www.opengis.net/wfs/2.0}FeatureType'):
        # Définir le nom de la couche 
        name = feature.find('{http://www.opengis.net/wfs/2.0}Name').text
        # Vérifier que le nom qui correspond a la couche à trouver
        if name == layer_name or name == f"ms:{layer_name}":
            # Créer une list pour les CRS possible avec le CRS par défault
            crs = [feature.find('{http://www.opengis.net/wfs/2.0}DefaultCRS').text]
            # Parcourir les autres CRS possible
            for other_crs in feature.findall('{http://www.opengis.net/wfs/2.0}OtherCRS'):
                crs.append(other_crs.text)
            # Retourner la liste formater la list des CRS
            return [c.replace("urn:ogc:def:crs:EPSG::", "EPSG:") for c in crs]
        
def layersPossibleCRS(wfs_server:str, layer_name:list[str]):
    """
    Permet de retourner la liste des WFS possible d'une list de couche WFS

    Args:
        wfs_server (str): Le lien vers le MapServer du WFS 
        layer_name (list[str]): Nom de la couche dans le MapServer du WFS

    Returns: Liste des CRS possible ex: ['EPSG:3798', 'EPSG:3799']
    """
    wfs_server = wfs_server.split("?")[0]
    wfs_server += "?service=WFS&version=2.0.0&request=GetCapabilities"
    # Fetch the WFS capabilities document with authentication and custom CA bundle
    response = requests.get(wfs_server, auth=HttpNegotiateAuth(), verify=False)
    # Vérifier que la réponse est valide
    if response.status_code != 200: return None

    # Parse the capabilities document
    capabilities = ET.fromstring(response.content)
    # Determiner l'élément qui contient les couches
    feature_list = capabilities.findall('{http://www.opengis.net/wfs/2.0}FeatureTypeList')[0]
    # Dictionnaire des CRS par couches
    layers_crs = {}
    # Parcourir les couche du mapserver
    for feature in feature_list.findall('{http://www.opengis.net/wfs/2.0}FeatureType'):
        # Définir le nom de la couche 
        name = feature.find('{http://www.opengis.net/wfs/2.0}Name').text
        name_1 = name.replace("ms:", "")
        name_2 = f"ms:{name_1}"
        # Vérifier que le nom qui correspond a la couche à trouver
        if name_1 in layer_name or name_2 in layer_name:
            # Créer une list pour les CRS possible avec le CRS par défault
            crs = [feature.find('{http://www.opengis.net/wfs/2.0}DefaultCRS').text]
            # Parcourir les autres CRS possible
            for other_crs in feature.findall('{http://www.opengis.net/wfs/2.0}OtherCRS'):
                crs.append(other_crs.text)
            # Liste formater des CRS
            crs = [c.replace("urn:ogc:def:crs:EPSG::", "EPSG:") for c in crs]
            # Ajouter la listes des CRS au bon nom de couche 
            if name_1 in layer_name: layers_crs[name_1] = crs
            else: layers_crs[name_2] = crs
    # Retourner le dictionnaire des CRS par couches
    return layers_crs
            