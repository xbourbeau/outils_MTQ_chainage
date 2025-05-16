# -*- coding: utf-8 -*-
import requests
try: from requests_negotiate_sspi import HttpNegotiateAuth
except: pass


def downloadFile(url:str, output_file:str, auth=True):
    """
    Permet de télécharger un fichier à partir d'un URL

    Args:
        url (str): L'url à utiliser pour le téléchargement
        output_file (str): Le fichier à enregistrer
        auth (bool): Utiliser une authentification pour le site

    Returns (bool): Success or not
    """
    try:
        # Send a GET request to the URL
        if auth: response = requests.get(url, stream=True, auth=HttpNegotiateAuth(), verify=False)
        else: response = requests.get(url, stream=True)
        
        # Vérifier que la réponse est valide
        if response.status_code != 200: return False
        # Open a local file in write-binary mode
        with open(output_file, 'wb') as file:
            # Write the content of the response to the local file in chunks
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    except: return False
    return True