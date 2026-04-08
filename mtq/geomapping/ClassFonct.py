# -*- coding: utf-8 -*-
from enum import Enum


class ClassFonct(Enum):
    AUTOROUTE = ("10", "Autoroute")
    NATIONALE = ("20", "Nationale")
    REGIONALE = ("30", "Régionale")
    COLLECTRICE = ("40", "Collectrice")
    LOCAL1 = ("51", "Local 1")
    LOCAL2 = ("52", "Local 2")
    LOCAL3 = ("53", "Local 3")
    ACCES_RESSOURCES = ("60", "Accès aux ressources")
    SANS_CLASSE = ("00", "Sans classe")
    NON_DEFINI = ("", "Non défini")

    def __init__(self, code, description):
        self.code = code
        self.description = description

    @classmethod
    def from_code(cls, code):
        for item in cls:
            if item.code == code: return item
        return cls.NON_DEFINI

    @classmethod
    def from_description(cls, desc):
        desc = desc.lower()
        for item in cls:
            if item.description.lower() == desc: return item
        return cls.NON_DEFINI
    
    @classmethod
    def from_text(cls, text:str):
        text = str(text).lower()
        for item in cls:
            if item.code == text: return item
            if item.description.lower() == text: return item
        return cls.NON_DEFINI

