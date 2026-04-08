# -*- coding: utf-8 -*-

class Axe:
    
    VALUES = {
        "A": "Conservation des chaussées",
        "B": "Conservation des structures",
        "C": "Amélioration du réseau",
        "D": "Développement du réseau",
        "E": "Structures - Réseau municipal",
        "F": "Développement (maritime)",
        "G": "Développement (aérien)",
        "H": "Amélioration (maritime)",
        "I": "Amélioration (aérien)",
        "K": "Voirie locale",
        "L": "Conservation (maritime)",
        "M": "Conservation (aérien)",
        "N": "Transport terrestre des personnes"
    }
    __slots__ = ("_code")

    def __init__(self, value:str):
        """
        Permet de définir un Axe de programmation

        Args:
            value (str): Le code ou le nom de l'axe
        """
        if value.upper() in self.VALUES: self._code = value.upper()
        else: self._code = {v: k for k, v in self.VALUES.items()}.get(value, None)

        if not self._code: raise ValueError(f"Axe inconnu : {value}")
    
    def __str__(self): return f"{self.code()} - {self.name()}"

    def __repr__(self): return f"Axe: {self.code()} - {self.name()}"
    
    def __eq__(self, other):
        if isinstance(other, Axe): return self.code() == other.code()
        else: return self.code() == other or self.name() == other or str(self) == other

    def __ne__(self, other):
        if isinstance(other, Axe): return self.code() != other.code()
        else: return self.code() != other and self.name() != other and str(self) != other

    def info(self):
        print("L'axe de programmation peut être l'un des valeurs suivantes:")
        for i, j in self.VALUES: print(i, j)
    
    def code(self): return self._code

    def name(self): return self.VALUES.get(self._code)
