# -- coding: utf-8 --
from .ElementInventaire import ElementInventaire
from ...geomapping.RTSS import RTSS
from ...geomapping.PolygonRTSS import PolygonRTSS 

class EspaceVert(ElementInventaire):

    __slots__ = ElementInventaire.__slots__ + ("rtss_debut", "rtss_fin", "_type", "types")

    def __init__(self):
        super().__init__()

        # Définition de l'élément d'inventaire Espaces Verts
        self.setCodeElement("VERT")

        # RTSS de début et de fin de l'espace vert
        self.rtss_debut = None
        self.rtss_fin = None
        self._type = None

        self.types = {
            "01":"Surface gazonnée",
            "02":"Fauchage",
            "03":"Aménagement paysager",
            "04":"Ouvrage de génie végétal",
            "05":"Friche",
            "06":"Haie brise-vent",
            "07":"Plantation",
            "08":"Milieu humide",
            "09":"Bosquet",
            "10":"Boisé",
            "99":"Non relevé"
        }

    def __str__(self): return f"Espace Vert IIT ({self.codeElement()})"

    def __repr__(self): return f"Espace Vert IIT ({self.codeElement()})"
    
    def __bool__ (self): return self.validate()

    def RTSSDebut(self, value:bool=False, formater:bool=False, zero:bool=True):
        """
        Retourner le RTSS de début de l'espace vert

        Args:
            value (bool, optional): Retourner la valeur de l'objet du RTSS
            formater (bool, optional): Formater le RTSS lorsque sa valeur est retournée.
            zero (bool, optional): Conserver les zéros à gauche du RTSS lors du formattage.
        """
        # Verifier si le RTSS de début est défini
        if self.rtss_debut is None: return None
        # Retourner la valeur du RTSS de début
        if value: return self.rtss_debut.value(formater=formater, zero=zero)
        # Retourner l'objet RTSS de début
        return self.rtss_debut
    
    def RTSSFin(self, value:bool=False, formater:bool=False, zero:bool=True):
        """
        Retourner le RTSS de fin de l'espace vert

        Args:
            value (bool, optional): Retourner la valeur de l'objet du RTSS
            formater (bool, optional): Formater le RTSS lorsque sa valeur est retournée.
            zero (bool, optional): Conserver les zéros à gauche du RTSS lors du formattage.
        """
        # Verifier si le RTSS de fin est défini
        if self.rtss_debut is None: return None
        # Retourner la valeur du RTSS de fin
        if value: return self.rtss_debut.value(formater=formater, zero=zero)
        # Retourner l'objet RTSS de fin
        return self.rtss_fin

    def setRTSS(self, rtss:RTSS):
        """
        Définir le RTSS de début et de fin de l'espace vert

        Args:
            rtss (RTSS/str): le RTSS de début et de fin de l'espace vert
        """
        self.setRTSSDebut(rtss)
        self.setRTSSFin(rtss)

    def setRTSSDebut(self, rtss:RTSS):
        """ Définir le RTSS de début de l'espace vert """
        self.rtss_debut = RTSS(rtss)
    
    def setRTSSFin(self, rtss:RTSS):
        """ Définir le RTSS de fin de l'espace vert """
        self.rtss_fin = RTSS(rtss)

    def setType(self, type):
        """
        Définir le type d'espace vert

        Args:
            type (str/int): Le code du type d'espace vert
        """
        type = str(type).zfill(2)
        if type in self.types: self._type = type
        else: raise ValueError(f"Type d'espace vert {type} invalide. "
                            f"Les types valides sont {self.types}")

    def setLocalisation(self, polygon_rtss:PolygonRTSS):
        """
        Définir les propriétés de localisation de l'espace vert.
        Soit le RTSS de début et de fin, le sens de relevé et l'emplacement.

        Args:
            polygon_rtss (PolygonRTSS): Le PolygonRTSS de l'espace vert
        """
        # Définir le RTSS de début et de fin de l'espace vert
        self.setRTSSDebut(polygon_rtss.getRTSS())
        self.setRTSSFin(polygon_rtss.getRTSS())
        # Définir le sens de relevé de l'espace vert
        self.setSensReleve("C")

        # Définir l'emplacement de l'espace vert selon le polygone RTSS
        if polygon_rtss.side() == 1: self.setEmplacement("D")
        elif polygon_rtss.side() == -1: self.setEmplacement("G")
        else: self.setEmplacement("C")

    def type(self, code=True):
        """
        Retourner le type d'espace vert

        Args:
            code (bool, optional): Retourner le code du type d'espace vert
        """
        if code: return self._type
        return self.types[self._type]

    def validate(self):
        """ Valider que l'élément d'inventaire à toute les informations nécessaires pour être exporté. """
        return all([self.sensReleve(),
                self.emplacement(),
                self.organismeGestion(),
                self.organismeEntretien(),
                self.RTSSDebut(),
                self.RTSSFin(),
                self.type()])

    def description(self):
        """ Retourner la liste des attributs de description de l'espace vert """
        return [
            self.RTSSDebut().getRoute(),
            self.RTSSDebut().getTroncon(),
            self.RTSSDebut().getSection(),
            self.RTSSDebut().getSousSection(),
            self.sensReleve(),
            self.emplacement(),
            self.type(),
            self.RTSSFin().getRoute(),
            self.RTSSFin().getTroncon(),
            self.RTSSFin().getSection(),
            self.RTSSFin().getSousSection(),
            self.typeEntretien(),
            self.organismeGestion(),
            self.organismeEntretien()
        ]




