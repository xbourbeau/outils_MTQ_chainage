# -*- coding: utf-8 -*-
import os.path
import subprocess
from datetime import datetime
import pyodbc
import pandas as pd

from ..geomapping.Geocodage import Geocodage

from .IdProjet import IdProjet
from .Axe import Axe
from .Projet import Projet


class PPS_ACCESS:

    T_PROJET = "TFICHE_PROJET"
    T_LOC = "TLOCALISATION_CARTO"
    T_ANNEE_TR = "PPS_ACC_CARTO_MONTN_PROG_PAR_ANN_TRV"
    T_DATE_PC = "R_DATE_PC_PROJET"
    C_NUM_PROJET = "NUM_PROJT"

    def __init__(self, geocode:Geocodage):
        self.default_dir = "//mtq/min/Donnees/PPS-ACCESS/PROD/DT90"
        # Vérifier si l'utilisateur à les accès au répertoire de PPS-ACCESS
        if not self.is_valide(): raise ConnectionError("Impossible d'acceder au repertoire. Vous devez demander les autorisations pour PPS-ACCESS")

        # Définir la base de donnée par défault à PPS-ACCESS Suivi
        self.set_default_database("Suivre")

        self.set_geocodage(geocode)

    def create_where_clause(self, list_of_projects:list[IdProjet, Projet]=[], where:str="", join="AND"):
        """
        Permet de retourner la une clause where pour une liste de projet et des clauses suplémentaire

        Args:
            list_of_projects (list[IdProjet, Projet], optional): Définir une liste de projet a utiliser pour la requete
            where (str, optional): La clause "where" de la requete SQL à utiliser. Defaults to aucune.
            join (str, optional): Opérateur à utiliser pour combinier les 2 expressions. Defaults to "AND"
        """
        where_clause = []
        # Ajouter une clause pour filtrer les projets
        if list_of_projects: where_clause.append(f"""{self.C_NUM_PROJET} IN ('{"','".join([str(IdProjet(str(i))) for i in list_of_projects])}')""")
        # Ajouter la clause suplémentaire
        if where: where_clause.append(f" {where}")
        # Retourner les 2 clauses joint
        return ' {join} '.join(where_clause)

    def set_geocodage(self, geocode:Geocodage):
        """
        Permet de définir un module de geocodage afin de calculer les géometries

        Args:
            geocode (Geocodage): Module de geocodage
        """
        if isinstance(geocode, Geocodage): self.geocode = geocode
        else: self.geocode = None

    def database_suivre(self):
        return os.path.realpath(os.path.join(self.folder(), "PPS-ACCESS_SUIVRE.accdb"))
    
    def database_planifier(self):
        return os.path.realpath(os.path.join(self.folder(), "PPS-ACCESS_PLANIFIER.accdb"))

    def default_database(self): return self._default_database

    def folder(self):
        """ Permet de retrouner le dossier de BD PPS-ACCESS """
        return os.path.join(os.environ["USERPROFILE"], "Documents/PPS-ACCESS")

    def get_list_projet(self, annee_min=None, annee_max=None, database=None):
        liste_project = []

        if annee_min or annee_max:
            where_clause = []
            if annee_min: where_clause.append(f"CInt(STR_AN) >= {annee_min}")
            if annee_max: where_clause.append(f"CInt(STR_AN) <= {annee_max}")
            where_clause = f"({' AND '.join(where_clause)})"
            data_annee = self.read_annee_tr(list_of_projects=liste_project, where=where_clause, database=database)
            liste_project = [info[self.C_NUM_PROJET] for i, info in data_annee.iterrows()]

        return liste_project

    def get_project(self, num_projet:IdProjet, localisation=False, annee_tr=False, pc=False, database=None):
        """
        Permet de retourner les informations pour un projet spécifique

        Args:
            num_projet (IdProjet): le numéro du projet PPS 
            geom (bool): Calculer leur géometrie ou pas. Défaults to False
            annee_tr(bool): Calculer leur années en travaux. Défaults to False
            pc(bool): Calculer leur point de controle. Défaults to False
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        projets = self.get_projects([num_projet], localisation=localisation, annee_tr=annee_tr, pc=pc, database=database)
        return projets.get(num_projet, None)

    def get_projects(self, num_projets:list[IdProjet], localisation=False, annee_tr=False, pc=False, database=None):
        """
        Permet de retourner les informations à partir d'une liste de projet et d'une condition suplémentaire

        Args:
            num_projet (list[IdProjet]): la liste des numéros de projet PPS 
            localisation (bool): Calculer leur localisation. Défaults to False
            annee_tr(bool): Calculer leur années en travaux. Défaults to False
            pc(bool): Calculer leur point de controle. Défaults to False
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        num_projets = [str(IdProjet(i)) for i in num_projets]        
        # Lire la BD et retourner le Pandas DataFrame
        data = self.read_fiche_projet(list_of_projects=num_projets, database=database)
        # Créer un dictionnaire des projets
        projets = {serie.get(self.C_NUM_PROJET): Projet.from_fiche_projet(serie) for i, serie in data.iterrows()}
        
        # Lire la table des localisations si besoin
        if localisation: data_loc = self.read_localisation_carto(list(projets.keys()), database=database)
        # Lire la table des années de travaux si besoin
        if annee_tr: data_annee = self.read_annee_tr(list(projets.keys()), database=database)
        # Lire la table des PC si besoin
        if pc: data_pc = self.read_date_pc(list(projets.keys()), database=database)
        
        # Parcourir les projets
        for p in projets.values():
            # Définir la localisation du projet si besoin 
            if localisation: p.set_localisation_from_table(data_loc[data_loc[self.C_NUM_PROJET] == p.numero_projet()])
            # Définir les années en travaux du projet si besoin 
            if annee_tr: p.set_annee_tr_from_table(data_annee[data_annee[self.C_NUM_PROJET] == p.numero_projet()])
            # Définir les dates de points de controle du projet si besoin 
            if pc: p.set_pc_from_table(data_pc[data_pc[self.C_NUM_PROJET] == p.numero_projet()])

        return projets

    def is_valide(self):
        """ Permet de vérifier si l'utilisateur à accès au répértoire """
        return os.path.exists(self.default_dir)
    
    def last_update_suivre(self, as_text=False):
        """ Permet de retourner la date de la dernière mise à jour de la BD suivi de la programmation """
        return self.last_update(database="Suivre", as_text=as_text)
    
    def last_update(self, database:str=None, as_text=False):
        """ Permet de retourner la date de la dernière mise à jour de la BD ACCESS """
        if database is None: database = self.default_database()
        
        if database == "Suivre": file_path = os.path.join(self.folder(), "0_MAJ_locale\FilesVersion_SUIVRE.ini")
        else: file_path = os.path.join(self.folder(), "0_MAJ_locale\FilesVersion_PLANIFIER.ini")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        last_update = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        if as_text: return last_update.strftime("%Y-%m-%d %H:%M:%S")
        else: return last_update

    def read(self, sql:str, database:str=None):
        """
        Permet de lire la BD PPS ACCESS et retourner l'info sous forme de DataFrame

        Args:
            sql (str): La commende SQL à utiliser pour lire la BD
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database

        Returns (DataFrame): Le résultat de la requete
        """
        if database is None: database == self.default_database()

        if database == "Suivre": database_path = self.database_suivre()
        else: database_path = self.database_planifier()

        conn_str = (
            r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
            f"DBQ={database_path}")
        conn = pyodbc.connect(conn_str)

        df = pd.read_sql(sql, conn)

        return df

    def read_table(self, table:str, list_of_projects:list[IdProjet, Projet]=[], where:str="", database:str=None):
        """
        Permet de retourner le contenu d'une table de PPS Access avec des options de filtre

        Args:
            table (str): le nom de la table à lire dans la BD
            list_of_projects (list[IdProjet, Projet]): Définir une liste de projet a utiliser pour la requete
            where (str, optional): :La clause "where" de la requete SQL à utiliser. Defaults to aucune.
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        # SQL de la requete 
        sql = f"SELECT * FROM {table}"
        where_clause = self.create_where_clause(list_of_projects=list_of_projects, where=where)
        
        if where_clause: sql += f" WHERE {where_clause}"
        return self.read(sql, database=database)

    def read_fiche_projet(self, list_of_projects:list[IdProjet, Projet]=[], where:str="", database:str=None):
        """
        Permet de retourner la table des fiches de projet de PPS Access

        Args:
            list_of_projects (list[IdProjet, Projet]): Définir une liste de projet a utiliser pour la requete
            where (str, optional): :La clause "where" de la requete SQL à utiliser. Defaults to aucune.
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        return self.read_table(self.T_PROJET, list_of_projects, where, database)

    def read_localisation_carto(self, list_of_projects:list[IdProjet, Projet]=[], where:str="", database:str=None):
        """
        Permet de retourner la table des fiches de projet de PPS Access

        Args:
            list_of_projects (list[IdProjet, Projet]): Définir une liste de projet a utiliser pour la requete
            where (str, optional): :La clause "where" de la requete SQL à utiliser. Defaults to aucune.
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        return self.read_table(self.T_LOC, list_of_projects, where, database)
    
    def read_annee_tr(self, list_of_projects:list[IdProjet, Projet]=[], where:str="", database:str=None):
        """
        Permet de retourner la table des montants programmer en travaux par années de PPS Access

        Args:
            list_of_projects (list[IdProjet, Projet]): Définir une liste de projet a utiliser pour la requete
            where (str, optional): :La clause "where" de la requete SQL à utiliser. Defaults to aucune.
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        return self.read_table(self.T_ANNEE_TR, list_of_projects, where, database)

    def read_date_pc(self, list_of_projects:list[IdProjet, Projet]=[], where:str="", database:str=None):
        """
        Permet de retourner la table des dates de point de controle des projets de PPS Access

        Args:
            list_of_projects (list[IdProjet, Projet]): Définir une liste de projet a utiliser pour la requete
            where (str, optional): :La clause "where" de la requete SQL à utiliser. Defaults to aucune.
            database (str): La database par défault à utiliser (Planifier|Suivre). Defaults to _default_database
        """
        return self.read_table(self.T_DATE_PC, list_of_projects, where, database)

    def set_default_database(self, database:str):
        """
        Permet de définir la database par défault à utiliser.

        Args:
            database (str): La database par défault à utiliser (Planifier|Suivre)
        """
        if database == "Planifier": self._default_database = "Planifier"
        else: self._default_database = "Suivre"
        return self._default_database

    def update(self, database:str=None):
        """
        Permet de lancer les mise à jour des BD si nécéssaire.

        Args:
            database (str): La database à utiliser (Planifier|Suivre). Défaults to Objet _default_database
        """
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        if database is None: database = self.default_database()
        
        if database == "Suivre": bat_file = os.path.realpath(os.path.join(self.default_dir, "PPS-ACCESS_SUIVRE_MAJ.bat"))
        else: bat_file = os.path.realpath(os.path.join(self.default_dir, "PPS-ACCESS_PLANIFIER_MAJ.bat"))

        subprocess.run(bat_file, startupinfo=startupinfo)



