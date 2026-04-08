# -*- coding: utf-8 -*-
import requests
import webbrowser
from ..packages.requests_negotiate_sspi import HttpNegotiateAuth
import json
import re

class ContentServer:

    def __init__(self):
        self.session = None
        # URL du dossier parent
        #parent_url = "https://gid.mtq.min.intra/otcs/llisapi.dll?func=ll&objId=170696591&objAction=browse&viewType=1"
        # Le nom du sous-dossier à trouver
        #target_name = "2025"

    def start_session(self):
        """
        Permet de démarrer la session avec les informations d'authentification windows pour
        ce connecter à SVN360.
        """
        try:
            self.session = requests.Session()
            self.session.auth = HttpNegotiateAuth()
            self.session.verify = False     
        except Exception as e:
            print(f"Error starting Content server session: {e}")
            self.session = None
        return not self.session is None
    
    def is_session_active(self):
        """
        Vérifie si la session est active.
        
        Returns:
            bool: True si la session est active, False sinon.
        """
        return self.session is not None

    def get_folder_url(self, parent_url:str, target_name:str):
        """
        Permet de trouver le lien pour ouvrir ContentServer en cherchant le nom d'un 
        sous-dossier à l'intérieur d'un dossier de départ

        Args:
            parent_url (str): Le chemin pour ouvrir le dossier parent dans lequel cherche le sous dossier
            target_name (str): Le nom du sous-dossier à trouver

        Returns: Le lien pour ouvrir le sous-dossier trouvé
        """
        if not self.is_session_active(): self.start_session()
        if not self.is_session_active(): raise Exception("Impossimble de démarer la session")
        # Ouvrir la page contentServer
        response = requests.get(parent_url, verify=False, auth=HttpNegotiateAuth())

        # Extract the JSON inside DataStringToVariables('...');
        match = re.search(r"DataStringToVariables\s*\(\s*'({.*})'\s*\)", response.text)
        if not match: raise Exception("Could not find DataStringToVariables() JSON in HTML.")
        # Parse JSON
        data = json.loads(match.group(1).replace('\\"', '"'))
        # Id de du dossier ContentServer trouvé
        target_id = None
        for row in data.get("myRows", []):
            # Parcourir les dossiers de ContentServer de la page web 
            for item, val in row.items():
                # Vérifier si le nom chercher et dans le nom du dossier
                if target_name.lower() in val.lower() and item == "name":
                    # Définir le data ID du dossier trouver
                    target_id = row.get("dataId", None)
                    # Retrouner le lien pour ouvrir le sous dossier
                    if target_id: return f"https://gid.mtq.min.intra/otcs/llisapi.dll?func=ll&objId={target_id}&objAction=browse&viewType=1"
                    else: return None
        return None