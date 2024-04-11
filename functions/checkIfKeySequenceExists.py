# -*- coding: utf-8 -*-

from qgis.gui import QgsGui

''' 
    Fonction qui vérifie si un QKeySequence est déjà assigné à une action dans l'application QGIS
    
    Entrée:
        - key_sequence(QKeySequence): Une séquence de touche du clavier ex: QKeySequence("Ctrl+C")
        
    Sortie:
        - bool: True = Le raccourcis existe déjà / False = Le raccourcis n'esxiste pas
'''

def checkIfKeySequenceExists(key_sequence):
    if QgsGui.shortcutsManager().actionForSequence(key_sequence): return True
    else: return False