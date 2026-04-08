# -*- coding: utf-8 -*-
from datetime import datetime
from pandas import Series

class PC:

    def __init__(self, numero:int, date_prevu=None, date_reel=None):
        self.numero = numero
        self.set_date_prevu(date_prevu)
        self.set_date_reel(date_reel)

    def __str__(self): return f"PC{self.numero}"

    def __repr__(self): 
        if self.is_done(): return f"{str(self)}: Date réel ({self.date_reel(True)})"
        elif self.is_planifier(): return f"{str(self)}: Date prévu ({self.date_prevu(True)})"
        else: return f"{str(self)} (Aucun)"

    def __eq__(self, other):
        if isinstance(other, PC): return self.id() == other.id()
        else: return self.id() == int(other)

    def __ne__(self, other):
        if isinstance(other, PC): return self.id() != other.id()
        else: return self.id() != int(other)

    def __lt__(self, other): 
        if isinstance(other, PC): return self.id() < other.id()
        else: return self.id() < int(int(other))

    def __le__(self, other): 
        if isinstance(other, PC): return self.id() <= other.id()
        else: return self.id() <= int(int(other))

    def __gt__(self, other):
        if isinstance(other, PC): return self.id() > other.id()
        else: return self.id() > int(int(other))

    def __ge__(self, other):
        if isinstance(other, PC): return self.id() >= other.id()
        else: return self.id() >= int(int(other))

    def id(self): return int(self.numero)

    def is_done(self): return self.date_reel() is not None

    def is_planifier(self): return self.date_prevu() is not None

    def set_date_prevu(self, date, format="%Y-%m-%d"):
        try: self._date_prevu = datetime.strptime(date, format)
        except: self._date_prevu = None

    def set_date_reel(self, date, format="%Y-%m-%d"):
        try: self._date_reel = datetime.strptime(date, format)
        except: self._date_reel = None

    def date_prevu(self, as_string=False):
        if self._date_prevu is None: return self._date_prevu
        if as_string: return self._date_prevu.strftime("%Y-%m-%d")
        else: return self._date_prevu

    def date_reel(self, as_string=False):
        if self._date_reel is None: return self._date_reel
        if as_string: return self._date_reel.strftime("%Y-%m-%d")
        else: return self._date_reel


class PC1(PC):

    def __init__(self, date_prevu=None, date_reel=None):
        super().__init__(1, date_prevu, date_reel)

    @classmethod
    def from_pps_access(cls, t_date_pc:Series):
        """
        Permet de créer un PC1 à partir du la Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 

        Args:
            t_date_pc (Series): Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 
        """
        date_prevu = t_date_pc.get("DAT_PREVU_PC1")
        date_reel = t_date_pc.get("DAT_REEL_PC1")
        return cls(date_prevu, date_reel)

class PC3(PC):

    def __init__(self, date_prevu=None, date_reel=None):
        super().__init__(3, date_prevu, date_reel)
    
    @classmethod
    def from_pps_access(cls, t_date_pc:Series):
        """
        Permet de créer un PC3 à partir du la Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 

        Args:
            t_date_pc (Series): Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 
        """
        date_prevu = t_date_pc.get("DAT_PREVU_PC3")
        date_reel = t_date_pc.get("DAT_REEL_PC3")
        return cls(date_prevu, date_reel)

class PC5(PC):

    def __init__(self, date_prevu=None, date_reel=None):
        super().__init__(5, date_prevu, date_reel)

    @classmethod
    def from_pps_access(cls, t_date_pc:Series):
        """
        Permet de créer un PC5 à partir du la Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 

        Args:
            t_date_pc (Series): Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 
        """
        date_prevu = t_date_pc.get("DAT_PREVU_PC5")
        date_reel = t_date_pc.get("DAT_REEL_PC5")
        return cls(date_prevu, date_reel)


class PC7(PC):

    def __init__(self, date_prevu=None, date_reel=None):
        super().__init__(7, date_prevu, date_reel)

    @classmethod
    def from_pps_access(cls, t_date_pc:Series):
        """
        Permet de créer un PC7 à partir du la Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 

        Args:
            t_date_pc (Series): Series (pandas) de la ligne d'un projet dans la table PPS ACCESS 
        """
        date_prevu = t_date_pc.get("DAT_PREVU_PC7")
        date_reel = t_date_pc.get("DAT_REEL_PC7")
        return cls(date_prevu, date_reel)