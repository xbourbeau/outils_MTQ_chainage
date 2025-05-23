# -- coding: utf-8 --
from .ElementInventaire import ElementInventaire
from ...geomapping.RTSS import RTSS
from ...geomapping.LineRTSS import LineRTSS 

class Marquage(ElementInventaire):

    __slots__ = ElementInventaire.__slots__ + ("rtss_debut", "rtss_fin", "_type", "types")

    def __init__(self):
        super().__init__()

        # Définition de l'élément d'inventaire du marquage
        self.setCodeElement("MARQ")

        # RTSS de début et de fin du marquage
        self.rtss_debut = None
        self.rtss_fin = None
        self._type = None

        self.types = {
            "01":"Surface gazonnée"
        }

    def __str__(self): return f"Marquage IIT ({self.codeElement()})"

    def __repr__(self): return f"Marquage IIT ({self.codeElement()})"
    
    def __bool__ (self): return self.validate()

    def RTSSDebut(self, value:bool=False, formater:bool=False, zero:bool=True):
        """
        Retourner le RTSS de début du Marquage

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
        Retourner le RTSS de fin du Marquage

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
        Définir le RTSS de début et de fin du Marquage
        Args:
            rtss (RTSS/str): le RTSS de début et de fin du Marquage
        """
        self.setRTSSDebut(rtss)
        self.setRTSSFin(rtss)

    def setRTSSDebut(self, rtss:RTSS):
        """ Définir le RTSS de début du Marquage """
        self.rtss_debut = RTSS(rtss)
    
    def setRTSSFin(self, rtss:RTSS):
        """ Définir le RTSS de fin du Marquage"""
        self.rtss_fin = RTSS(rtss)

    def setType(self, type):
        """
        Définir le type du marquage

        Args:
            type (str/int): Le code du Marquage
        """
        type = str(type).zfill(2)
        if type in self.types: self._type = type
        else: raise ValueError(f"Type de marquage {type} invalide. "
                            f"Les types valides sont {self.types}")

    def setLocalisation(self, line_rtss:LineRTSS):
        """
        Définir les propriétés de localisation du Marquage.
        Soit le RTSS de début et de fin, le sens de relevé et l'emplacement.

        Args:
            polygon_rtss (LineRTSS): Le LineRTSS du Marquage
        """
        # Définir le RTSS de début et de fin du Marquage
        self.setRTSSDebut(line_rtss.getRTSS())
        self.setRTSSFin(line_rtss.getRTSS())
        # Définir le sens de relevé du Marquage
        self.setSensReleve("C")

        # Définir l'emplacement du Marquage selon la LineRTSS
        if line_rtss.side() == 1: self.setEmplacement("D")
        elif line_rtss.side() == -1: self.setEmplacement("G")
        else: self.setEmplacement("C")

    def type(self, code=True):
        """
        Retourner le type du marquage

        Args:
            code (bool, optional): Retourner le code du type du marquage
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
        """ Retourner la liste des attributs de description du marquage """
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
    
    @staticmethod
    def getCodeTypeLigne(type_ligne):
        """ Permet de retourner le code IIT du type de ligne du marquage longitudinal """
        if type_ligne == 'Simple discontinue':
            return '01'
        elif type_ligne == 'Simple continue':
            return '02'
        elif type_ligne == u'Double discontinue à droite':
            return '03'
        elif type_ligne == u'Double discontinue à gauche':
            return '04'
        elif type_ligne == 'Double continue':
            return '05'
        elif type_ligne == 'Double discontinue':
            return '06'
        else:
            return ''
        
    @staticmethod
    def getCodeCouleur(couleur):
        """ Permet de retourner le code IIT de la couleur du marquage longitudinal """
        if couleur == 'Blanc':
            return '01'
        elif couleur == 'Jaune':
            return '02'
        elif couleur == 'Rouge':
            return '03'
        elif couleur == u'Blanc sur fond noir':
            return '05'
        else:
            return ''
    
    @staticmethod        
    def getCodeTypeMat(type_mat):
        """ Permet de retourner le code IIT du matériaux du marquage longitudinal """
        if type_mat == u'Bandes préfabriquées':
            return '01'
        elif type_mat == 'MMA':
            return '22'
        elif type_mat == u"Produits expérimentaux":
            return '23'
        elif type_mat == u"Peinture à l'alkyde":
            return '45'
        elif type_mat == u"Peinture à l'époxy":
            return '46'
        elif type_mat == u"Peinture à l'eau":
            return '47'
        else:
            return '99'

    @staticmethod
    def getCodeSousType(self, sous_type):
        """ Permet de retourner le code IIT du sous type de ligne du marquage longitudinal """
        if sous_type == u'Ligne axiale':
            return '01'
        elif sous_type == u'Ligne délimitation deux voies et plus même sens':
            return '02'
        elif sous_type == u'Ligne de délimitation de voie à circulation alternée':
            return '03'
        elif sous_type == u'Ligne délimitation voie réservée virage gauche deux sens':
            return '04'
        elif sous_type == u'Ligne délimitation voie réservée':
            return '05'
        elif sous_type == u'Ligne délimitation voie de dépassement':
            return '06'
        elif sous_type == u'Ligne délimitation voie véhicules lents':
            return '07'
        elif sous_type == u'Ligne de rive':
            return '08'
        elif sous_type == u'Ligne de continuité':
            return '09'
        elif sous_type == u'Ligne de guidage':
            return '10'
        elif sous_type == u"Ligne d'abord d'obstacles":
            return '11'
        elif sous_type == u"Ligne de céder le passage":
            return '12'
        else:
            return ''




