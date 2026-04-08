# -*- coding: utf-8 -*-
from typing import Union
import pandas as pd
import os
import webbrowser

from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem

from ..geomapping.Geocodage import Geocodage
from ..system.ContentServer import ContentServer

from .IdProjet import IdProjet
from .Axe import Axe
from .PC import PC1, PC3, PC5, PC7, PC
from .LocalisationProjet import LocalisationProjet

class Projet:
    """
    Un objet qui permet de représenter un projet du MTQ dans le sytème PSS et
    identifiable par un numéro de projet unique (IdProjet).
    """

    def __init__(self, num_projet:Union[IdProjet, int, str], **kwargs):
        """
        Créer un objet projet PPS

        Args:
            num_projet (IdProjet): Numéro unique du projet
        """
        self.num_projet = IdProjet(num_projet)

        # Attibuts suplémentaire possible
        self.set_axe(kwargs.get("axe", None))
        self.set_intervention(kwargs.get("intervention", None))
        self.set_localisation(kwargs.get("loc", {}))
        self.set_annee_tr(kwargs.get("annee_min", None), kwargs.get("annee_max", None))
        self.set_pc(kwargs.get("pc", {}))

        # Conserver toute les autres attributs
        self.attributs = kwargs

    @classmethod
    def from_fiche_projet(cls, fiche_projet:pd.Series):
        return cls(fiche_projet.get("NUM_PROJT"), axe=fiche_projet.get("COD_AXE_INTRN"), **fiche_projet.to_dict())
    
    def __str__ (self): return self.numero_projet(formater=True)

    def __int__ (self): return self.numero_projet(as_int=True)

    def __repr__(self): return f"Projet: {self.numero_projet(True)} ({str(self.axe())})"

    def __getitem__(self, index): return self.attributs[index]

    def __hash__(self): return hash(self.numero_projet())

    def annee_tr(self):
        """ Permet de retrourner la liste des années dont des travaux sont prévue """
        if self._annee_min and self._annee_max: return list(range(self._annee_min, self._annee_max + 1))
        if self._annee_min: return [self._annee_min]
        if self._annee_max: return [self._annee_max]

    def axe(self): 
        """ Permet de retrourner l'axe de programmation du projet """
        return self._axe

    def dossier_p(self):
        """ Permet de retourner le dossier du P: si existant """
        dossier_possible = os.path.realpath(f"//Mtq.min.intra/fic/ESTRIE/Espace Collaboratif/projets/{self.numero_projet(formater=True)}")
        if os.path.exists(dossier_possible): return dossier_possible
        return None

    def id(self):
        """ Permet de retourner numéro d'identification unique du projet """
        return self.num_projet

    def numero_projet(self, formater=False, as_int=False):
        """
        Permet de retourner numéro d'identification unique du projet sous forme de text ou entier

        Args:
            formater (bool, optional): Retourner le numéro de projet sous forme de text formater. Defaults to False.
            as_int (bool, optional): Retourner le numéro de projet sous en chiffre entier. Defaults to False.
        """
        if formater: return self.id().value_formater()
        if as_int: return int(self.id())
        return str(self.id())
    
    def open_dossier_p(self):
        """ Permet d'ouvrir le dossier du P: si existant """
        dossier = self.dossier_p()
        if dossier: os.startfile(dossier)

    def set_annee_tr(self, annee_min:int, annee_max:int):
        """
        Permet de définir la période des travaux du projet

        Args:
            annee_min (int): Année minimum des travaux du projet
            annee_max (int): Année maximum des travaux du projet
        """
        if annee_min: self._annee_min = int(annee_min)
        else: self._annee_min = None
        if annee_max: self._annee_max = int(annee_max)
        else: self._annee_max = None

    def set_annee_tr_from_table(self, t_annee_tr:pd.DataFrame):
        annee = [info_projet["STR_AN"] for i, info_projet in t_annee_tr.iterrows()]
        self.set_annee_tr(min(annee), max(annee))
            
    def set_axe(self, axe:Union[Axe, str]):
        """
        Permet de définir l'axe de programmation du projet

        Args:
            axe (Axe): L'axe de programmation du projet
        """
        if axe: self._axe = Axe(axe)
        else: self._axe = None

    def set_intervention(self, intervention:str):
        """
        Permet de définir le type d'intervention du projet

        Args:
            intervention (str): Le type d'intervention du projet
        """
        self._intervention = intervention

    def set_localisation(self, loc:dict[int, LocalisationProjet]):
        """
        Permet de définir le dictionaire du dictionnaire
        Args:
            loc (dict[int, LocalisationProjet]): Dictionnaire des localisations du projet
        """
        self._localisation = loc

    def set_localisation_from_table(self, t_loc_carto:pd.DataFrame):
        locs = {}
        for i, loc in t_loc_carto.iterrows():
            loc_projet = LocalisationProjet.from_pps_access(loc)
            locs[loc_projet.id()] = loc_projet
            
        self.set_localisation(locs)

    def set_pc(self, dict_pc:dict[int, PC]):
        """
        Permet de définir les points de contrôle du projet

        Args:
            dict_pc (dict[int, PC]): Le dictionnaire qui contient les différents PC du projet
        """
        self.dict_pc = dict_pc
    
    def set_pc_from_table(self, t_pc:pd.DataFrame):
        locs = {}
        for i, serie_proj in t_pc.iterrows():
            locs[1] = PC1.from_pps_access(serie_proj)
            locs[3] = PC3.from_pps_access(serie_proj)
            locs[5] = PC5.from_pps_access(serie_proj)
            locs[7] = PC7.from_pps_access(serie_proj)
        self.set_pc(locs)

    def open_gid_pcr(self):
        content_server = ContentServer()
        content_server.start_session()
        
        annee = self.id().list_sections()[1]
        if int(annee) > 70: annee = f"19{annee}"
        else: annee = f"20{annee}"
        
        parent_url = "https://gid.mtq.min.intra/otcs/llisapi.dll?func=ll&objId=170696591&objAction=browse&viewType=1"
        new_parent = content_server.get_folder_url(parent_url, annee)
        dossier_projet = content_server.get_folder_url(new_parent, str(self.id()))

        if dossier_projet: webbrowser.open(dossier_projet)

    def open_gid_pc7(self):
        content_server = ContentServer()
        content_server.start_session()
        
        annee = self.id().list_sections()[1]
        if int(annee) > 70: annee = f"19{annee}"
        else: annee = f"20{annee}"

        dossier_1 = "D - CONSTRUCTION ET SURVEILLANCE"
        dossier_2 = "D905"
        
        parent_url = "https://gid.mtq.min.intra/otcs/llisapi.dll?func=ll&objId=170696591&objAction=browse&viewType=1"
        new_parent = content_server.get_folder_url(parent_url, annee)
        
        dossier_projet = content_server.get_folder_url(new_parent, str(self.id()))
        dossier_1 = content_server.get_folder_url(dossier_projet, dossier_1)
        dossier_2 = content_server.get_folder_url(dossier_1, dossier_2)

        
        if dossier_2: webbrowser.open(dossier_2)
