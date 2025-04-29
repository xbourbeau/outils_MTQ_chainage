# -*- coding: utf-8 -*-
import os
import shutil
from datetime import datetime

from qgis.core import (QgsVectorFileWriter, QgsFields, QgsField, QgsFeature,
                       QgsGeometry, QgsCoordinateReferenceSystem, QgsVectorLayerUtils,
                       QgsCoordinateTransformContext, QgsProject)
from PyQt5.QtCore import QVariant

from ...fnt.reprojections import reprojectGeometry
from .ElementInventaire import ElementInventaire
from .EspaceVert import EspaceVert

class SystemIIT:

    def __init__(self):
        # Séparateur utiliser par les fichiers textes 
        self.separateur = ";"
        
        # Dictionnaire des transactions possible
        self.transactions = {
            "A": "Ajout",
            "M":"Modification descriptive",
            "G":"Modification géométrique",
            "S":"Suppression",
            "N":"Non modifié"
        }
        # Dictionnaire des méthodes de relevé possible
        self.methodes_releve = {
            "01": "GPS Absolu",
            "02": "Imagerie Verticale",
            "03": "Imagerie Horizontale",
            "04": "Photogrammétrie",
            "05": "Arpentage par GPS",
            "10": "GPS avec décalage par repport à la trace",
            "11": "Imagerie Verticale avec décalage par repport à la trace",
            "12": "Photogrammétrie avec décalage par repport à la trace",
            "20": "Odomèetre electronique",
            "21": "GPS, chainage avec décalage trace",
            "22": "Imagerie verticale (vidéo terrestre) (par chainage - distance trace)"}
        
        # Dictionnaire des précisions possible
        self.precisions = {
            "01": "Moins de 1m",
            "02":"De 1 à 3m",
            "03": "Moins de 3m"
        }

        self.offset_id = 100_000
    
    def help(self):
        os.startfile("http://gid.mtq.min.intra/otcs/llisapi.dll?func=ll&objId=375590571&objAction=browse&viewType=1")
    
    def createAjouts(self,
                     liste_element_iit:list[ElementInventaire],
                     output_path:str,
                     methode_releve:str="04",
                     precision:str="02"):
        """
        Créer les fichiers de chargement IIT pour une liste d'éléments d'inventaire à ajouter.

        Args:
            liste_element_iit (list[ElementInventaire]): La liste des éléments d'inventaire à ajouter
            output_path (str): Le repertoire de sortie pour les fichiers de chargement
            methode_releve (str, optional): Le code de la méthode de relevé. Defaults to "04".
            precision (str, optional): Le code de la précision. Defaults to "02".
        """
        # Vérifier si la liste des éléments d'inventaire est vide
        if liste_element_iit is None or len(liste_element_iit) == 0:
            raise ValueError("La liste des éléments d'inventaire est vide.")
        # Vérifier si la liste des éléments d'inventaire contient des éléments d'inventaire différent
        elif not all(isinstance(elem, type(liste_element_iit[0])) for elem in liste_element_iit):
            raise ValueError("La liste des éléments d'inventaire contient des éléments d'inventaire différent.")
        
        # Définir le nom du répertoire pour les fichiers de chargement
        folder = os.path.dirname(output_path)
        # Vérifier si le répertoire de sortie existe
        if not os.path.exists(folder): raise FileNotFoundError(f"Le répertoire {folder} n'existe pas.")
        # Vérifier si le répertoire de sortie à créer existe
        if os.path.exists(output_path): raise FileExistsError(f"Le répertoire {output_path} existe déjà.")
        # Créer le répertoire de sortie
        os.makedirs(output_path)
        
        try:
            # Créer le fichier de métadonnée
            self.writeMetadata(os.path.join(output_path, "metadata.txt"), methode_releve, precision)
            # Créer le fichier de description
            self.writeDescription(liste_element_iit, os.path.join(output_path, "description.txt"), "A")
            # Créer le fichier de localisation
            self.writeLocalisation(liste_element_iit, os.path.join(output_path, "localisation"))
        except Exception as e:
            # Supprimer le répertoire de sortie
            shutil.rmtree(output_path)
            # Retourner l'erreur
            raise e
        
        return True

    def date(self):
        """ Retourne la date du jour pour les fichiers de chargement """
        return datetime.today().strftime("%Y-%m-%d")
    
    def getMethodeReleve(self, methode_releve:str):
        """ Retourne la méthode de relevé selon le code spécifié """
        # Ajouter un zéro devant le code si nécessaire
        methode_releve = str(methode_releve).zfill(2)
        # Vérifier si le code est valide
        if methode_releve in self.methodes_releve: return methode_releve
        else:
            raise ValueError(f"La méthode de relevé {methode_releve} n'est pas valide. "
                             f"Les méthodes valides sont: {self.methodes_releve}")
        
    def getPrecision(self, precision:str):
        """ Retourne la précision selon le code spécifié """
        # Ajouter un zéro devant le code si nécessaire
        precision = str(precision).zfill(2)
        # Vérifier si le code est valide
        if precision in self.precisions: return precision
        else:
            raise ValueError(f"La précision {precision} n'est pas valide. "
                             f"Les précisions valides sont: {self.precisions}")
        
    def getTransaction(self, transaction:str):
        """ Retourne la transaction selon le code spécifié """
        # Vérifier si le code est valide
        if transaction in self.transactions: return transaction
        else:
            raise ValueError(f"La transaction {transaction} n'est pas valide. "
                             f"Les transactions valides sont: {self.transactions}")

    def writeMetadata(self, output_file:str, methode_releve:str, precision:str):
        """
        Écrire le fichier de métadonnée de relevé dans un fichier texte.

        Args:
            output_file (str): Le chemin du fichier de sortie
            methode_releve (str): Le code de la méthode de relevé
            precision (str): Le code de la précision
        """
        # Vérifier si le répertoire de sortie existe
        if not os.path.exists(os.path.dirname(output_file)): raise FileNotFoundError(f"Le répertoire {output_file} n'existe pas.")
        # Déterminer la méthode de relevé
        methode_releve = self.getMethodeReleve(methode_releve)
        # Déterminer la précision
        precision = self.getPrecision(precision)
        
        # Écrire les informations dans le fichier
        with open(output_file, 'w') as meta:
            meta.write(methode_releve + self.separateur + precision)
        
        return True
    
    def writeDescription(self, liste_element_iit:list[ElementInventaire], output_file:str, code_transaction:str):
        """
        Écrire le fichier de descriptions des éléments d'inventaire.

        Args:
            liste_element_iit (list[ElementInventaire]): La liste des éléments d'inventaire à écrire
            output_file (str): Le chemin du fichier de sortie
            code_transaction (str): Le code de la transaction à effectuer
        """
        # Vérifier si le répertoire de sortie existe
        if not os.path.exists(os.path.dirname(output_file)): raise FileNotFoundError(f"Le répertoire {output_file} n'existe pas.")
        # Déterminer la transaction
        code_transaction = self.getTransaction(code_transaction)
        # Liste des lignes de description
        lines = []
        # Parcourir les éléments d'inventaire de la liste
        for i, elem in enumerate(liste_element_iit):
            # Vérifier si l'élément d'inventaire est valide
            if not elem.validate():
                raise ValueError(f"Élément (#{i}) est invalide.")
            # Créer le début de description de l'élément d'inventaire
            desc = [
                elem.codeElement(code=True),
                code_transaction,
                self.date(),
                str(self.offset_id+i)
            ]
            # Ajouter les attributs de description spécifique de l'élément d'inventaire
            desc.extend(elem.description())
            # Ajouter la ligne de description de l'élément d'inventaire à la liste
            lines.append(self.separateur.join(desc))
        
        # Écrire les informations dans le fichier
        with open(output_file, 'w') as desc_file:
            # Écrire les lignes de description dans le fichier
            desc_file.write("\n".join(lines))
        
        return True

    def writeLocalisation(self, liste_element_iit:list[ElementInventaire], output_folder:str):
        """
        Écrire le fichier de localisation des éléments d'inventaire.

        Args:
            liste_element_iit (list[ElementInventaire]): La liste des éléments d'inventaire à écrire
            output_file (str): Le chemin du fichier de sortie
        """
        repertoire = os.path.dirname(output_folder)
        # Vérifier si le répertoire de sortie existe
        if not os.path.exists(repertoire): raise FileNotFoundError(f"Le répertoire {repertoire} n'existe pas.")
        if os.path.exists(output_folder): raise FileExistsError(f"Le fichier {output_folder} existe déjà.")
        
        # Créer le repertoire de sortie pour les fichiers mapinfo
        os.makedirs(output_folder)

        # Create output filename
        output_file = os.path.join(output_folder, "localisation.tab")
        
        # Setup fields
        fields = QgsFields()
        fields.append(QgsField("NoObjet", QVariant.String))
        
        # Setup writer options
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "MapInfo File"
        
        # Parcourir les éléments d'inventaire de la liste
        feats = []
        for i, elem in enumerate(liste_element_iit):
            feat = QgsFeature()
            feat.setGeometry(
                reprojectGeometry(
                    elem.geometry(),
                    QgsCoordinateReferenceSystem("EPSG:3798"),
                    QgsCoordinateReferenceSystem("EPSG:4269")))
            feat.setAttributes([str(self.offset_id + i)])
            feats.append(feat)

        # Create writer
        writer = QgsVectorFileWriter.create(
            output_file,
            fields,
            elem.geometry().wkbType(),
            QgsCoordinateReferenceSystem("EPSG:4269"),
            QgsCoordinateTransformContext(),
            options)
        writer.addFeatures(feats)
        # Close writer
        del writer

        # Créer un fichier IND vide avec le fichier mapinfo
        with open(os.path.join(output_folder, "localisation.IND"), 'w') as ind:
            ind.write("")

        # Create zip file
        shutil.make_archive(
            base_name=os.path.join(repertoire, "localisation"),
            format='zip',
            root_dir=output_folder)

        return True

