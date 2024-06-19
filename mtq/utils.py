# -*- coding: utf-8 -*-
import time
from qgis.PyQt.QtWidgets import QMessageBox

class Utilitaire:

    def __init__(self):
        self.timer = None

    def getMessageSubject(self, level, custom_subject=None):
        if custom_subject is not None: return custom_subject
        if level == 0: return "Info: " 
        elif level == 1: return "Warning: "
        elif level == 2: return "Error: "
        elif level == 3: return "Succes: "
        else: return ""

    def afficherMessageQGIS(self, iface, message, level=1, temps=5, subject=None):
        """
        Méthode qui affiche un message dans la barre de messages de l'interface QGIS.

        Args:
            iface: L'interface QGIS.
            message (str): Le message à afficher.
            level (int): 0 = Info, 1 = Warning, 2 = Critical, 3 = Success
            temps (int): seconde d'affichage
            subject (str): Sujet du message (gras:)
        """
        subject = self.getMessageSubject(level, subject)
        messageQGIS = iface.messageBar().createMessage(subject, message)
        iface.messageBar().pushWidget(messageQGIS, level, temps)

    @staticmethod
    def criticalMessage(iface, message, temps=5, subject=None):
        """
        Méthode statique qui affiche un message critique dans la barre de messages de l'interface QGIS.

        Args:
            iface: L'interface QGIS.
            message (str): Le message à afficher.
            temps (int): seconde d'affichage
            subject (str): Sujet du message (gras:)
        """
        Utilitaire().afficherMessageQGIS(iface, message, level=2, temps=temps, subject=subject)

    @staticmethod
    def InfoMessage(iface, message, temps=5, subject=None):
        """
        Méthode statique qui affiche un message critique dans la barre de messages de l'interface QGIS.

        Args:
            iface: L'interface QGIS.
            message (str): Le message à afficher.
            temps (int): seconde d'affichage
            subject (str): Sujet du message (gras:)
        """
        Utilitaire().afficherMessageQGIS(iface, message, level=0, temps=temps, subject=subject)

    @staticmethod
    def succesMessage(iface, message, temps=5, subject=None):
        """
        Méthode statique qui affiche un message critique dans la barre de messages de l'interface QGIS.

        Args:
            iface: L'interface QGIS.
            message (str): Le message à afficher.
            temps (int): seconde d'affichage
            subject (str): Sujet du message (gras:)
        """
        Utilitaire().afficherMessageQGIS(iface, message, level=3, temps=temps, subject=subject)

    @staticmethod
    def warningMessage(iface, message, temps=5, subject=None):
        """
        Méthode statique qui affiche un message critique dans la barre de messages de l'interface QGIS.

        Args:
            iface: L'interface QGIS.
            message (str): Le message à afficher.
            temps (int): seconde d'affichage
            subject (str): Sujet du message (gras:)
        """
        Utilitaire().afficherMessageQGIS(iface, message, level=1, temps=temps, subject=subject)

    @staticmethod
    def warningQuestion(title, message):
        answer = QMessageBox.warning(
            QMessageBox(),
            title,
            message,
            QMessageBox.Yes | QMessageBox.No)
        return answer == QMessageBox.Yes

    @staticmethod
    def printTime(start_time, sujet):
        """
        Imprime la durée d'exécution d'un bloc de code.

        Args:
            start_time (float): Le temps de début de l'exécution du bloc de code.
            sujet (str): Le sujet ou la description du bloc de code.
        """
        execution_time = time.time() - start_time
        print(f"Durée d'exécution ({sujet}) : {execution_time} secondes")
        return 
    
    def startTimer(self): self.timer = time.time()

    def endTimer(self): return time.time() - self.timer

    def printTimer(self, sujet=""):
        self.printTime(self.endTimer(), sujet=sujet)