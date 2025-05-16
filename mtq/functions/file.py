# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QFileDialog
import os.path

def choisirDossier(window_name="Choisir le dossier", default_folder=""):
    """
    Fonction qui ouvre une fenêtre de dialog pour que l'utilisateur choisi un dossier.

    Args:
        - window_name (str): Nom de la fenêtre à créer
        - default_folder (str): Le dossier par défault
    """
    if os.path.exists(default_folder): folder = default_folder
    else: folder = os.path.expanduser("~") + '\Desktop\\'
    chemin = QFileDialog.getExistingDirectory(None, window_name, folder)
    
    if os.path.exists(chemin): return chemin + '/'
    else: return default_folder

def saveFichier(window_name="Enregistrer le fichier", ext=".geojson", default_file=""):
    """
    Fonction qui ouvre une fenêtre de dialog pour que l'utilisateur enregistre un fichier.

    Args: 
        - window_name (str): Nom de la fenêtre à créer
        - ext (str): Extention du fichier à enregistrer (incluant le point)
        - default_file (str): Le dossier par défault
    """
    folder = os.path.expanduser("~") + '\Desktop\\'
    if default_file:
        default_file = os.path.realpath(default_file)
        # Conserver le nom du dossier où est enregistré le fichier 
        if os.path.exists(os.path.dirname(default_file)): folder = default_file
    file, extention = QFileDialog.getSaveFileName(None, window_name, folder, ext)
    if file:  return file
    else: return default_file

def choisirFichier(window_name="Choisir le fichier", ext=".txt", default_file=""):
    """
    Fonction qui ouvre une fenêtre de dialog pour que l'utilisateur choisi un fichier.

    Args: 
        - window_name (str): Nom de la fenêtre à créer
        - ext (str): Extention du fichier à choisir (incluant le point)
        - default_file (str): Le dossier par défault
    """
    folder = os.path.expanduser("~") + '\Desktop\\'
    if default_file:
        # Conserver le nom du dossier où est enregistré le fichier 
        if os.path.exists(default_file): folder = default_file
        
    file, extention = QFileDialog.getOpenFileName(None, window_name, folder, ext)
    if os.path.exists(file): return file
    else: return default_file