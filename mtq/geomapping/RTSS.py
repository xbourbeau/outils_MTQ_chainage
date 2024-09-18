from typing import Dict

class RTSS:
    """ 
    Un objet qui représente un RTSS (route-tronçon-section-sous route)
    selon la définition du ministère.
    Ex. 00112-01-200-000C
    """
    __slots__ = ("num_rts", "attributs")

    def __init__(self, num_rts:str, **kwargs):
        """
        Constructeur de l'objet RTSS

        Args:
            - num_rts (str/int): Le rtss à définir
            - kwargs (dict): Attributs du RTSS
        """
        self.set(num_rts)
        self.attributs = kwargs

    def __str__ (self): return self.value()
    
    def __repr__ (self): return f"RTSS: ({self.value(True)})"

    def __len__(self): return len(self.value())

    def __getitem__(self, index): return self.value[index]

    def __hash__(self): return hash(self.value())

    def __eq__(self, other):
        if isinstance(other, RTSS): return self.value() == other.value()
        else: return self.value() == RTSS.verifyFormatRTSS(other)

    def __ne__(self, other):
        if isinstance(other, RTSS): return self.value() != other.value()
        else: return self.value() != RTSS.verifyFormatRTSS(other)

    def __lt__(self, other): 
        if isinstance(other, RTSS): return self.value() < other.value()
        else: return self.value() < RTSS.verifyFormatRTSS(other)

    def __le__(self, other): 
        if isinstance(other, RTSS): return self.value() <= other.value()
        else: return self.value() <= RTSS.verifyFormatRTSS(other)

    def __gt__(self, other):
        if isinstance(other, RTSS): return self.value() > other.value()
        else: return self.value() > RTSS.verifyFormatRTSS(other)

    def __ge__(self, other):
        if isinstance(other, RTSS): return self.value() >= other.value()
        else: return self.value() >= RTSS.verifyFormatRTSS(other)

    def getAttribut(self, name):
        """ Permet de retrourner une valeurs d'attribut du RTSS """
        return self.attributs.get(name, None)
    
    def getAttributs(self)->Dict:
        """ Permet de retrourner le dictionnaire des attributs du RTSS """
        return self.attributs
    
    def getAttributsName(self)->list:
        """ Permet de retrourner une liste des noms des attributs du RTSS """
        return list(self.attributs.keys())
    
    def getAttributsValues(self)->list:
        """ Permet de retrourner une liste des valeurs des attributs du RTSS """
        return list(self.attributs.values())

    def getChausse(self)->str:
        """ Permet de retourner le dernier caractère du rtss sois C, D, G ou 0 """
        return self.num_rts[-1]

    def getRTS(self, formater=False, zero=True)->str:
        """ Permet de retourner seulement la route, tronçon et section """
        jointure = "-" if formater else ""
        return jointure.join(self.listSections(sous_section=False, zero=zero))

    def getRoute(self, as_int=False, zero=True):
        """ 
        Méthode qui renvoie le numéro de la route
        Ex: 00116-01-120-000C => 00116
        
        Args:
            - as_int (bool): retourner le numéro sous forme de chiffre
            - zero (bool): Conserver les zéro au début du numéro de route
        """
        if as_int: return int(self.num_rts[:5])
        else: 
            if zero: return self.num_rts[:5]
            else: return str(int(self.num_rts[:5]))
    
    def getTroncon(self, as_int=False):
        """ 
        Méthode qui renvoie le numéro de troncon du RTSS
        Ex: 00116-01-120-000C => 01

        Args:
            - as_int (bool): retourner le numéro sous forme de chiffre
        """
        if as_int: return int(self.num_rts[5:7])
        else: return self.num_rts[5:7]
        
    def getSection(self, as_int=False):
        """ 
        Méthode qui renvoie le numéro de section du RTSS
        Ex: 00116-01-120-000C => 120
        
        Args:
            - as_int (bool): retourner le numéro sous forme de chiffre
        """
        if as_int: return int(self.num_rts[7:10])
        else: return self.num_rts[7:10]
        
    def getSousSection(self)->str:
        """ 
        Méthode qui renvoie la sous-section du RTSS
        Ex: 00116-01-120-000C => 000C
        """
        return self.num_rts[10:]

    def hasPartOf(self, value):
        """ Permet de vérifier si la valeur est dans le numéro de RTSS """
        return value in self.value() or value in self.value(formater=True)

    def hasAttribut(self, name):
        """ Permet de vérifier si le RTSS à un attribut selon sont nom """
        return name in self.attributs

    def isValide(self):
        """ Vérifier que la longueur du RTSS est de 14"""
        return len(self) == 14

    def listSections(self, route=True, troncon=True, section=True, sous_section=True, zero=True)->list:
        """
        Permet de retourner une liste contenant chaque section du RTSS.
        
        Args:
            - route (bool): Retourner la route dans la liste
            - troncon (bool): Retourner le troncon dans la liste
            - section (bool): Retourner la section dans la liste
            - sous_section (bool): Retourner la sous-section dans la liste
            - zero (bool): Conserver les zéro au début du numéro de route
        """
        # Liste des différentes partie du RTSS
        sections = []
        # Ajouter le numéro de la route
        if route: sections.append(self.getRoute(zero=zero))
        # Ajouter le numéro du tronçon
        if troncon: sections.append(self.getTroncon())
        # Ajouter le numéro de la section
        if section: sections.append(self.getSection())
        # Ajouter le numéro de la sous-section
        if sous_section: sections.append(self.getSousSection())
        # Retourner la liste des différentes partie du RTSS
        return sections
    
    def set(self, value):
        """
        Permet définir le numéro du rtss.

        Args:
            - value (str/int): Le rtss à définir
        """
        #if not isinstance(value, str): value = str(value)
        #if " " in value: value = value.replace(" ", "")
        #if "-" in value: value = value.replace('-', '')
        #if len(value) >= 11:  value = value.rjust(14, '0')
        value = RTSS.verifyFormatRTSS(value)
        if len(value) != 14: raise ValueError("Le numero du RTSS est invalide, il doit contenir 14 caracteres")
        self.num_rts = value
    
    def setAttribut(self, name, value):
        """
        Permet de définir un attribut du RTSS.

        Args:
            - name (str): Le nom de l'attribut à définir
            - value (any): La valeur de l'attribut
        """
        self.attributs[name] = value

    def startWith(self, value):
        """ Permet de vérifier si la valeur est le début du RTSS"""
        value = str(value).upper()
        if value == self.value()[:len(value)]: return True
        if value == self.value(formater=True)[:len(value)]: return True
        if value == self.value(zero=False)[:len(value)]: return True
        if value == self.value(formater=True, zero=False)[:len(value)]: return True
        return False

    def value(self, formater=False, zero=True)->str:
        """ 
        Permet d'obtenir le numéro du RTSS. Celui-ci peux être formater ou non.

        Args:
            - formater (bool): Indique si le RTSS retourné doit être formater
            - zero (bool): Conserver les zéro au début
        """
        if formater: return "-".join(self.listSections(zero=zero))
        elif zero: return self.num_rts 
        else: return "".join(self.listSections(zero=zero))
    
    def valueFormater(self)->str:
        """ Permet d'obtenir le numéro du RTSS formater """
        return self.value(formater=True)
    

    def verifyFormatRTSS(rtss):
        """
        Fonction qui permet de toujours renvoyer un rtss non formater valide.

        Args:
            - rtss (str): Le rtss à vérifier
        """
        if not isinstance(rtss, str): rtss = str(rtss)
        if " " in rtss: rtss = rtss.replace(" ", "")
        if "-" in rtss: rtss = RTSS.deformaterRTSS(rtss)
        if len(rtss) >= 11:  rtss = rtss.rjust(14, '0')
        rtss = rtss.upper()
        return rtss
    
    
    def formaterRTSS(rtss, inverse=False):
        """
        Formater un numéro de RTSS avec des tirets.
        ex: 0001001210000C -> 00010-01-210-000C

        Args:
            - rtss (str): Le numéro de projet à formater
            - inverse (bool): True=[00010-01-210-000C => 0001001210000C] False=[0001001210000C => 00010-01-210-000C] 
        """
        if inverse: return rtss.replace('-', '')
        else: return f"{rtss[:5]}-{rtss[5:7]}-{rtss[7:10]}-{rtss[10:]}"


    def deformaterRTSS(rtss):
        """
        Déformater un numéro de RTSS avec des tirets.
        ex: 00010-01-210-000C -> 0001001210000C

        Args:
            - rtss (str): Le numéro de projet à formater
        """
        return RTSS.formaterRTSS(rtss, inverse=True)