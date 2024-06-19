# -*- coding: utf-8 -*-
from typing import Union

class Chainage:
    """ 
    Un objet qui représente une valeur de chainage selon la définition du ministère.
    Ex. 2+293
    """

    __slots__ = ("chainage")

    def __init__(self, chainage:Union[str, int, float]):
        """
        Constructeur de l'objet Chainage

        Args:
            - chainage (str/real): Le chainage à définir
        """
        self.set(chainage)

    def __str__ (self): return str(self.value())

    def __int__(self): return int(self.value())

    def __float__(self): return float(self.value())

    def __hash__(self): return hash(self.value())

    def __repr__ (self): return f"Chainage: ({self.valueFormater()})"

    def __lt__(self, other): 
        if isinstance(other, Chainage): 
            return self.value() < other.value()
        else: 
            return self.value() < Chainage.verifyFormatChainage(other)

    def __le__(self, other): 
        if isinstance(other, Chainage): 
            return self.value() <= other.value()
        else: 
            return self.value() <= Chainage.verifyFormatChainage(other)

    def __eq__(self, other):
        if isinstance(other, Chainage): 
            return self.value() == other.value()
        else: 
            return self.value() == Chainage.verifyFormatChainage(other)

    def __ne__(self, other):
        if isinstance(other, Chainage): 
            return self.value() != other.value()
        else: 
            return self.value() != Chainage.verifyFormatChainage(other)

    def __gt__(self, other):
        if isinstance(other, Chainage): 
            return self.value() > other.value()
        else: 
            return self.value() > Chainage.verifyFormatChainage(other)

    def __ge__(self, other):
        if isinstance(other, Chainage): 
            return self.value() >= other.value()
        else: 
            return self.value() >= Chainage.verifyFormatChainage(other)

    def __sub__(self, other):
        if isinstance(other, Chainage): 
            return Chainage(self.value() - other.value())
        else: 
            return Chainage(self.value() - Chainage.verifyFormatChainage(other))

    def __add__(self, other):
        if isinstance(other, Chainage): 
            return Chainage(self.value() + other.value())
        else: 
            return Chainage(self.value() + Chainage.verifyFormatChainage(other))

    def __mul__(self, other):
        if isinstance(other, Chainage): 
            return Chainage(self.value() * other.value())
        else: 
            return Chainage(self.value() * Chainage.verifyFormatChainage(other))

    def __truediv__(self, other):
        if isinstance(other, Chainage): 
            return Chainage(self.value() / other.value())
        else: 
            return Chainage(self.value() / Chainage.verifyFormatChainage(other))

    def __round__(self, ndigits): 
        self.set(self.value(precision=ndigits))
        return self

    def set(self, value):
        """
        Permet définir la valeur du chainage.

        Args:
            - value (str/int): Le chainage à définir
        """
        try:
            if ',' in str(value): 
                value = value.replace(",", ".")
            if '+' in str(value): 
                value =  float(Chainage.deformaterChainage(value))
            else: 
                value = float(value)
        except: 
            raise ValueError("La valeur du chainage n'est pas valide")

        self.chainage = value
    
    def value(self, formater=False, precision=None):
        """ 
        Permet d'obtenir le numéro du chainage. Celui-ci peux être formater ou non.

        Args:
            - formater (bool): Indique si le chainage retourné doit être formater
            - precision (int): Précision du chainage à retourner
        """
        # Retourner le chainage formater
        if formater: 
            return Chainage.formaterChainage(self.chainage, precision=precision)
        # Retourner le chainage numérique
        else: 
            if precision is None: 
                return self.chainage
            else: 
                return round(self.chainage, precision)

    def valueFormater(self, precision=None):
        """
        Permet d'obtenir le numéro du chainage formater
        
        Args:
            - precision (int): Précision du chainage à retourner
        """
        return self.value(formater=True, precision=precision)
    

    def verifyFormatChainage(chainage):
        """
        Fonction qui permet de toujours renvoyer un chainage numérique.

        Args:
            - chainage (numeric/str): Le chainage à vérifier
        """
        try:
            if ',' in str(chainage): 
                chainage = chainage.replace(",", ".")
            if '+' in str(chainage): 
                return float(Chainage.deformaterChainage(chainage))
            else: 
                return float(chainage)
        except: 
            return None


    def formaterChainage(chainage, precision=None, inverse=False):
        """
        Fonction qui convertie un chaînage numérique à un chaînage formater textuellement
        Ex: chaînage numérique (0000.0) -> chaînage formater (0+000.0)

        Args:
            - chainage (str/numeric): Le chainage à convertir
            - precision (int): Le nombre determinant la valeur pour à arrondire
            - inverse (bool): True=[2+498 => 2498] False=[2498 => 2+498] 
        """
        # chaînage formater --> chaînage numérique
        if inverse:
            # Déterminer la précision si elle n'est pas déterminé
            if precision is None:
                if '.' in chainage: 
                    precision = len(chainage[chainage.find('.')+1:])
                else: 
                    precision = 0
            # Séparer les milliers et les centaines par le "+"
            millier, centaine = chainage.split('+')
            # Convertir les milliers et les centaines en nombre
            val_convertie = int(millier) * 1000 + float(centaine)
            # Arrondir la valeur selon la précision définie
            val_convertie = round(val_convertie, precision)
            # Convertir en nombre entier si la précision est de 0 ou moins
            if precision <= 0: 
                val_convertie = int(val_convertie)
            # Retourner la valeur formatée
            return val_convertie
        # chaînage numérique --> chaînage formater
        else:
            # Déterminer la précision si elle n'est pas déterminé
            if precision is None: 
                precision = (
                    [round(chainage, i) == round(chainage,3) 
                     for i in [0, 1, 2, 3]].index(True)
                )
            
            # Determiner si le format est entier ou réel
            if precision <= 0: # Entier
                # Calculer le chainage arrondie selon la précision définie
                chainage = int(round(chainage, precision))
                # Format à appliquer pour un nombre entier
                number_format = '{:03}'
            else: # Réel
                # Format à appliquer pour un nombre réel avec la précision définie
                number_format = '{:0%i.%if}' % (4 + precision, precision)
            # Déterminer les milliers
            millier = int(chainage / 1000)
            # Retourner le nombre selon le formatage définie 
            return str(millier) + "+" + number_format.format(chainage - (millier*1000))       

    def deformaterChainage(chainage, precision=None):
        """
        Fonction qui convertie un chaînage formater à un chaînage numérique
        Ex: chaînage formater (0+000.0) -> chaînage numérique (0000.0)

        Args:
            - chainage (str/float/int): Le chainage à convertir
            - precision (int): Le nombre determinant la valeur pour à arrondire
        """
        return Chainage.formaterChainage(chainage, precision, inverse=True)