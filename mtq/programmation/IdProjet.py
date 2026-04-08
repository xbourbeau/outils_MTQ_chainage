# -*- coding: utf-8 -*-
from typing import Dict, Union

class IdProjet:
    """ 
    Un objet qui représente un identifiant unique d'un projet dans le système PPS.
    """
    __slots__ = ("num_projet", "attributs")

    def __init__(self, num_projet:Union[str, int], **kwargs):
        """
        Constructeur de l'objet IdProjet

        Args:
            - num_projet (str/int): Le numéro du projet à définir
            - kwargs (dict): Attributs du numéro du projet
        """
        self.set(num_projet)
        self.attributs = kwargs

    def __str__ (self): return self.value()

    def __int__ (self): return int(self.num_projet)
    
    def __repr__ (self): return f"Numero projet: ({self.value(True)})"

    def __len__(self): return len(self.value())

    def __getitem__(self, index): return self.value[index]

    def __hash__(self): return hash(self.value())

    def __eq__(self, other):
        if isinstance(other, IdProjet): return self.value() == other.value()
        else: return self.value() == IdProjet.verify_format(other)

    def __ne__(self, other):
        if isinstance(other, IdProjet): return self.value() != other.value()
        else: return self.value() != IdProjet.verify_format(other)

    def __lt__(self, other): 
        if isinstance(other, IdProjet): return int(self.value()) < int(other.value())
        else: return int(self.value()) < int(IdProjet.verify_format(other))

    def __le__(self, other): 
        if isinstance(other, IdProjet): return int(self.value()) <= int(other.value())
        else: return int(self.value()) <= int(IdProjet.verify_format(other))

    def __gt__(self, other):
        if isinstance(other, IdProjet): return int(self.value()) > int(other.value())
        else: return int(self.value()) > int(IdProjet.verify_format(other))

    def __ge__(self, other):
        if isinstance(other, IdProjet): return int(self.value()) >= int(other.value())
        else: return int(self.value()) >= int(IdProjet.verify_format(other))

    def get_attribut(self, name):
        """ Permet de retrourner une valeurs d'attribut du numéro de projet """
        return self.attributs.get(name, None)
    
    def get_attributs(self)->Dict:
        """ Permet de retrourner le dictionnaire des attributs du numéro de projet """
        return self.attributs
    
    def get_attributs_name(self)->list:
        """ Permet de retrourner une liste des noms des attributs du numéro de projet """
        return list(self.attributs.keys())
    
    def get_attributs_values(self)->list:
        """ Permet de retrourner une liste des valeurs des attributs du numéro de projet """
        return list(self.attributs.values())

    def get(self, formater=False)->str:
        """ Permet de retourner le numéro de projet """
        jointure = "-" if formater else ""
        return jointure.join(self.listSections())

    def has_part_of(self, value):
        """ Permet de vérifier si la valeur est dans le numéro de projet """
        return value in self.value() or value in self.value(formater=True)

    def has_attribut(self, name):
        """ Permet de vérifier si le numéro de projet à un attribut selon sont nom """
        return name in self.attributs

    def is_valide(self):
        """ Vérifier que la longueur du numéro de projet est de 9 et commence par 154"""
        return len(self) == 9 and self.num_projet.startswith("154")
    
    def list_sections(self):
        """ Permet de retourner une liste avec les 3 sections du numéro de projet. """
        return [self.num_projet[:3], self.num_projet[3:5], self.num_projet[5:]]

    def set(self, value):
        """
        Permet définir le numéro du projet.

        Args:
            - value (str/int): Le numéro du projet à définir
        """
        value = IdProjet.verify_format(value)
        if len(value) != 9: raise ValueError("Le numero du projet est invalide, il doit contenir exactement 9 chiffre")
        if not value.startswith("154"): raise ValueError("Le numero du projet est invalide, il doit commencer par 154")
        self.num_projet = value
    
    def set_attribut(self, name, value):
        """
        Permet de définir un attribut du numéro de projet.

        Args:
            - name (str): Le nom de l'attribut à définir
            - value (any): La valeur de l'attribut
        """
        self.attributs[name] = value

    def value(self, formater=False)->str:
        """ 
        Permet d'obtenir le numéro du projet. Celui-ci peux être formater ou non.

        Args:
            - formater (bool): Indique si le numéro du projet retourné doit être formater
        """
        if formater: return "-".join(self.list_sections())
        else: return self.num_projet
    
    def value_formater(self)->str:
        """ Permet d'obtenir le numéro du numéro de projet formaté """
        return self.value(formater=True)
    
    @staticmethod
    def verify_format(num_projet):
        """
        Fonction qui permet de toujours renvoyer un numéro de projet non formater valide.

        Args:
            - num_projet (str): Le numéro de projet à vérifier
        """
        if not isinstance(num_projet, str): num_projet = str(num_projet)
        num_projet = ''.join(ch for ch in num_projet if '0' <= ch <= '9')
        return num_projet
    
    @staticmethod
    def formater(num_projet:str, inverse=False):
        """
        Formater un numéro de projet avec des tirets.
        ex: 154182345 -> 154-18-2345

        Args:
            - num_projet (str): Le numéro de projet à formater
            - inverse (bool): True=[154-18-2345 => 154182345] False=[154182345 => 154-18-2345] 
        """
        if inverse: return num_projet.replace('-', '')
        else: return f"{num_projet[:3]}-{num_projet[3:5]}-{num_projet[5:]}"

    @staticmethod
    def deformater(num_projet):
        """
        Déformater un numéro de projet avec des tirets.
        ex: 154-18-2345 -> 154182345

        Args:
            - num_projet (str): Le numéro de projet à formater
        """
        return IdProjet.formater(num_projet, inverse=True)