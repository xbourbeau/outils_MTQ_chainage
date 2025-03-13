# -- coding: utf-8 --
from abc import ABC, abstractmethod

class ElementInventaire(ABC):
    """
    Classe permettant de définir un élément d'inventaire routier.

    Attributes:
        organism_entretien (str): Type d'organisme d'entretien
        organism_gestion (str): Type d'organisme gestionnaire
        type_entretien (str): Type d'entretien
        sens_releve (str): Sens du relevé
        code_emplacement (str): Emplacement
        geom (any): Geometry de l'élément d'inventaire
        type_organisme (dict): Dictionnaire des types d'organismes possible
        sens_releves (dict): Sens du relevé possible
        codes_emplacement (dict): Emplacements possible
        types_entretien (dict): Types d'entretien possible
    """

    __slots__ = ("organism_entretien", "organism_gestion", "type_entretien",
                 "sens_releve", "code_emplacement", "geom", "type_organisme",
                 "sens_releves", "codes_emplacement", "types_entretien", "code_element")

    def __init__(self):
        """ Constructeur de l'objet ElementInventaire """
        # Type d'organisme d'entretien
        self.organism_entretien = None
        # Type d'organisme gestionnaire
        self.organism_gestion = None
        # Type d'entretien
        self.type_entretien = None
        # Sens du relevé
        self.sens_releve = None
        # Emplacement
        self.code_emplacement = None
        # Code de l'élément d'inventaire
        self.code_element = None
        # Geometry de l'élément d'inventaire
        self.geom = None

        # Dictionnaire des types d'organismes possible
        self.type_organisme = {
            "01":"Gouvernement du Québec",
            "02":"Gouvernement fédéral",
            "03":"Autres gouvernements",
            "04":"Régional",
            "05":"Université",
            "06":"Entreprise privée",
            "07":"Organisme public de transport (OPT)",
            "08":"Conseil intermunicipal de transport (CIT)",
            "09":"Organisme municipal et intermunicipal de transport (OMIT)",
            "10":"Organisme de transport adapté (OTA)",
            "11":"Para-public",
            "12":"Municipalité",
            "14":"Partenariat public-privé",
            "15":"Organisme sans but lucratif",
            "16":"Propriétaire privé",
            "99":"Inconnu"}
        
        # Sens du relevé possible
        self.sens_releves = {
            "C": "Sens du chainage",
            "I": "Sens inverse du chainage"
        }

        # Emplacements possible
        self.codes_emplacement = {
            "G": "Gauche",
            "D": "Droite",
            "C": "Centre",
            "CD": "Centre-droite",
            "CG": "Centre-gauche"
        }

        # Types d'entretien possible
        self.types_entretien = {
            "01": "Ministère",
            "02": "Contract",
            "03": "Propriétaire privé",
            "04": "Autre"
        }

        # Types de codes d'élément d'inventaire possible
        self.code_element = {
            "BORD":"Bordure",
            "CLOT":"Cloture",
            "COND":"Drainage conduite",
            "COUR":"Courbe",
            "DISP":"Dispositif de retenue",
            "ELEM":"Éléments divers",
            "EXDR":"Extrémité de drainage",
            "ILOT":"Ilot",
            "LONG":"Marque longitudinale sur la chaussée",
            "AUTR":"Marque transversale sur la chaussée et autres marques",
            "MUR":"Mur d'extrémité de drainage",
            "MUS":"Musoir",
            "OCCU":"Occupation actuelle",
            "PEN":"Pente",
            "PONC":"Drainage ponctuel",
            "SERV":"Servitude ou permission",
            "TERR":"Terre-plein",
            "TROT":"Trottoir",
            "VERT":"Espace vert",
            "VOIE":"Voie de circulation",
            "SEMC":"Segment de marque longitudinale",
            "SEVC":"Segment de voie de circulation",
            "IMAG":"Image"
        }

    def __str__(self): return "ElementInventaire IIT"

    def __repr__(self): return "ElementInventaire IIT"

    def organismeGestion(self, code=True):
        """
        Permet de retourner le type d'organisme gestionnaire de l'élément d'inventaire

        Args:
            code (bool, optional): Retourner le code ou la description. Defaults to True.

        Returns: Retourne le code ou la description de l'organisme gestionnaire
        """
        # Vérifier si l'organisme gestionnaire est défini
        if not self.organism_gestion: raise ValueError("L'organisme gestionnaire n'a pas été défini")
        # Retourner le code ou la description de l'organisme gestionnaire
        if code: return self.organism_gestion
        else: return self.type_organisme[self.organism_gestion]

    def organismeEntretien(self, code=True):
        """
        Permet de retourner le type d'organisme d'entretien de l'élément d'inventaire

        Args:
            code (bool, optional): Retourner le code ou la description. Defaults to True.

        Returns: Retourne le code ou la description de l'organisme d'entretien
        """
        # Vérifier si l'organisme d'entretien est défini
        if not self.organism_entretien: raise ValueError("L'organisme d'entretien n'a pas été défini")
        # Retourner le code ou la description de l'organisme d'entretien
        if code: return self.organism_entretien
        else: return self.type_organisme[self.organism_entretien]

    def setOrganisme(self, type_organisme):
        """
        Permet de définir le type d'organisme gestionnaire et d'entretien de l'élément d'inventaire

        Args:
            type_organisme (str/int): Code du type d'organisme
        """
        self.setOrganismeGestion(type_organisme)
        self.setOrganismeEntretien(type_organisme)

    def setOrganismeGestion(self, type_organisme):
        """
        Permet de définir le type d'organisme gestionnaire de l'élément d'inventaire

        Args:
            type_organisme (str/int): Code du type d'organisme
        """
        type_organisme = str(type_organisme).zfill(2)
        if type_organisme in self.type_organisme: self.organism_gestion = type_organisme
        else: raise ValueError(f"Type organisme {type_organisme} invalide. "
                               f"Les types valides sont {self.type_organisme}")
    
    def setOrganismeEntretien(self, type_organisme):
        """
        Permet de définir le type d'organisme d'entretien de l'élément d'inventaire

        Args:
            type_organisme (str/int): Code du type d'organisme

        Returns: Vrai si le type d'organisme est valide, sinon faux
        """
        type_organisme = str(type_organisme).zfill(2)
        if type_organisme in self.type_organisme: self.organism_entretien = type_organisme
        else: raise ValueError(f"Type organisme {type_organisme} invalide. "
                                f"Les types valides sont {self.type_organisme}")
    
    def sensReleve(self, code=True):
        """
        Permet de retourner le sens du relevé de l'élément d'inventaire

        Args:
            code (bool, optional): Retourner le code ou la description. Defaults to True.

        Returns: Retourne le code ou la description du sens du relevé
        """
        # Vérifier si le sens de relevé est défini
        if not self.sens_releve: raise ValueError("Le sens de relevé n'a pas été défini")
        # Retourner le code ou la description du sens de relevé
        if code: return self.sens_releve
        else: return self.sens_releves[self.sens_releve]

    def setSensReleve(self, sens_releve):
        """
        Permet de définir le sens du relevé de l'élément d'inventaire

        Args:
            sens_releve (str): Code du sens du relevé

        Returns: Vrai si le sens du relevé est valide, sinon faux
        """
        if sens_releve in self.sens_releves: self.sens_releve = sens_releve
        else: raise ValueError(f"Sens de relevé {sens_releve} invalide"
                                f"Les sens valides sont {self.sens_releves}")

    def emplacement(self, code=True):
        """
        Permet de retourner l'emplacement de l'élément d'inventaire

        Args:
            code (bool, optional): Retourner le code ou la description. Defaults to True.

        Returns: Retourne le code ou la description de l'emplacement
        """
        # Vérifier si l'emplacement est défini
        if not self.code_emplacement: raise ValueError("L'emplacement n'a pas été défini")
        # Retourner le code ou la description de l'emplacement
        if code: return self.code_emplacement
        else: return self.codes_emplacement[self.code_emplacement]
    
    def setEmplacement(self, code_emplacement):
        """
        Permet de définir l'emplacement de l'élément d'inventaire

        Args:
            code_emplacement (str): Code de l'emplacement

        Returns: Vrai si l'emplacement est valide, sinon faux
        """
        if code_emplacement in self.codes_emplacement: self.code_emplacement = code_emplacement
        else: raise ValueError(f"Emplacement {code_emplacement} invalide. "
                            f"Les emplacements valides sont {self.codes_emplacement}")

    def typeEntretien(self, code=True):
        """
        Permet de retourner le type d'entretien de l'élément d'inventaire

        Args:
            code (bool, optional): Retourner le code ou la description. Defaults to True.

        Returns: Retourne le code ou la description du type d'entretien
        """
        # Renvoyer rien si le type d'entretien n'est pas défini
        if not self.type_entretien: return ""
        # Retourner le code ou la description du type d'entretien
        if code: return self.type_entretien
        else: return self.types_entretien[self.type_entretien]

    def setTypeEntretien(self, type_entretien):
        """
        Permet de définir le type d'entretien de l'élément d'inventaire

        Args:
            type_entretien (str/int): Code du type d'entretien

        Returns: Vrai si le type d'entretien est valide, sinon faux
        """
        type_entretien = str(type_entretien).zfill(2)
        if type_entretien in self.types_entretien: self.type_entretien = type_entretien
        else: raise ValueError(f"Type d'entretien {type_entretien} invalide. "
                            f"Les types valides sont {self.types_entretien}")
    
    def geometry(self):
        """
        Permet de retourner la géométrie de l'élément d'inventaire

        Returns: Retourne la géométrie de l'élément d'inventaire
        """
        return self.geom
    
    def setGeometry(self, geom):
        """
        Permet de définir la géométrie de l'élément d'inventaire

        Args:
            geom (any): Géométrie de l'élément d'inventaire
        """
        self.geom = geom

    def codeElement(self, code=True):
        """
        Permet de retourner le code de l'élément d'inventaire

        Args:
            code (bool, optional): Retourner le code ou la description. Defaults to True.

        Returns: Retourne le code ou la description de l'élément d'inventaire
        """
        # Vérifier si le code de l'élément d'inventaire est défini
        if not self.code_element: raise ValueError("Le code de l'élément d'inventaire n'a pas été défini")
        # Retourner le code ou la description de l'élément d'inventaire
        if code: return self.code_element
        else: return self.code_element[self.code_element]

    def setCodeElement(self, code_element):
        """
        Permet de définir le code de l'élément d'inventaire

        Args:
            code_element (str): Code de l'élément d'inventaire

        Returns: Vrai si le code de l'élément d'inventaire est valide, sinon faux
        """
        if code_element in self.code_element: self.code_element = code_element
        else: raise ValueError(f"Code d'élément {code_element} invalide. "
                            f"Les codes valides sont {self.code_element}")
    
    @abstractmethod
    def description(self):
        """ Permet de retourner la liste des attributs nécéssaire à la description de l'élément d'inventaire """
        pass

    @abstractmethod
    def validate(self):
        """ Permet de valider l'élément d'inventaire """
        pass