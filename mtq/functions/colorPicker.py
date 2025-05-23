# -*- coding: utf-8 -*-

from qgis.core import QgsFeatureRequest, QgsVectorLayer
import random
from copy import deepcopy

def colorPicker(layer:QgsVectorLayer, pallette:list, champ_couleur="color", requete:str=None):
    """
    Fonction qui permet de choisir une couleur pour chaque entitées d'une couche en fonction de 
    sa proximité avec les autres entitées de la couche. Le nombre de couleur devrait être supérieur
    aux nombres d'entitées pouvant être superposé (distance 0).
    
    Args:
        - layer (QgsVectorLayer): La couche à choisir les couleurs
        - pallette (list): Une list de valeurs unique représentant les couleurs
        - champ_couleur (str): Le champ contennat les valeurs de couleur
        - requete (str): Une requête à appliquer pour filtrer les entitées
    """
    # Nombre max de feature à vérifier la proximité
    feat_number = len(pallette)-1
    # La position du champ dans la couche
    field_id = [field.name() for field in layer.fields()].index(champ_couleur)
    request = QgsFeatureRequest()
    if requete: request.setFilterExpression(requete)
    # Mettre la couche en édition si elle ne l'est pas
    if not layer.isEditable(): layer.startEditing()
    # Parcourir les entités de la couche 
    for feat1 in layer.getFeatures(request):
        # Liste des features proche
        list_feat = []
        # Liste des distances des features
        distances = []
        # Reparcourir chaque entités de la couche 
        for feat2 in layer.getFeatures(request):
            # Ignorer l'entité en cours
            if feat2 != feat1:
                # Calculer la distance
                dist = feat1.geometry().distance(feat2.geometry())
                # Vérifier si la list est pleine
                if len(list_feat) == feat_number:
                    # Vérifier si la distance est plus petite que la plus gande de la liste
                    if dist < max(distances):
                        # Trouver la position dans la liste de la distance à retirer 
                        idx_to_remove = distances.index(max(distances))
                        # Retirer les valeurs des listes
                        list_feat.pop(idx_to_remove)
                        distances.pop(idx_to_remove)
                        # Ajouter les nouvelles valeurs
                        list_feat.append(feat2)
                        distances.append(dist)
                else:
                    # Ajouter les valeurs aux listes
                    list_feat.append(feat2)
                    distances.append(dist)
        # Copier la pallette de couleur original
        pallette_choice = deepcopy(pallette)
        # Parcourir les entitées les plus proche
        for feat in list_feat:
            # Indentifier leurs couleurs
            color  = feat[champ_couleur]
            # Retirer la couleur de la pallette des choix possible
            if color in pallette_choice: pallette_choice.remove(color)
        # Choisir une couleur aléatoire dans la pallette resultante
        color_picked = random.choice(pallette_choice)
        # Modifier le champ de couleurs de la couche 
        layer.changeAttributeValue(feat1.id(), field_id, color_picked)