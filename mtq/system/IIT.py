# -*- coding: utf-8 -*-
import os

class IIT:

    def __init__(self):
        # Current date
        #self.date = datetime.datetime.today().strftime('%Y-%m-%d')
        #self.output_dir = r"C:\Users\xbourbeau\Desktop"
        self.separateur = ";"
        self.user_iit = "NBOXC"
        
        # Nom des fichiers à écrire
        self.metadata_filename = "metadata.txt"
        self.description_filename = "description.txt"
        self.localisation_filename = "localisation.txt"
        
        self.trasactions = {"A": "Ajout", "M":"Modification descriptive", "G":"Modification géométrique", "S":"Suppression", "N":"Non modifié"}
        self.methodes_releve = {
            "01": "GPS Absolu",
            "02": "Imagerie Verticale",
            "03": "Imagerie Horizontale",
            "04": "Photogrammétrie",
            "05": "Arpentage par GPS",
            "10": "GPS avec décalage par repport à la trace",
            "11": "Imagerie Verticale avec décalage par repport à la trace",
            "12": "Photogrammétrie avec décalage par repport à la trace",
            "20": "Odomèetre electronique",
            "21": "GPS, chainage avec décalage trace",
            "22": "Imagerie verticale (vidéo terrestre) (par chainage - distance trace)"}
            
        self.precisions = {"01": "Moins de 1m", "02":"De 1 à 3m", "03": "Moins de 3m"}
    
    def help(self):
        os.startfile("http://gid.mtq.min.intra/otcs/llisapi.dll?func=ll&objId=375590571&objAction=browse&viewType=1")
    
    def setTransaction(self, code):
        if code in self.trasactions: self.code_transaction = code
        else: self.code_transaction = None
        return self.code_transaction
    
    def setMethodeReleve(self, code):
        if code in self.methodes_releve: self.methode_releve = code
        else: self.methode_releve = None
        return self.methode_releve
    
    def setPrecision(self, code):
        if code in self.precisions: self.precision = code
        else: self.precision = None
        return self.precision
    
    def writeMetadate(self, methode_releve=None, precision=None):
        if methode_releve: self.setMethodeReleve(methode_releve)
        if precision: self.setMethodeReleve(precision)
        
        if self.methode_releve and self.precision:
            if os.path.exists(self.output_dir):
                metadata = os.path.join(self.output_dir, self.metadata_filename)
                with open(metadata, 'w') as meta:
                    meta.write(self.methode_releve + self.separateur + self.precision)
                return True
        return False
        
    def writeDescription(self):
        pass

    @staticmethod
    def getMRCByCode(code):
        """ Permet de retourner le nom de la MRC selon le code inscrit dans IIT """
        code = str(code)
        if code == '30': return "Le Granit"
        elif code == '40': return "Les Sources"
        elif code == '41': return "Le Haut-Saint-François"
        elif code == '42': return "Le Val-Saint-François"
        elif code == '43': return "Sherbrooke"
        elif code == '44': return "Coaticook"
        elif code == '45': return "Memphrémagog"
        elif code == '46': return "Brome-Missisquoi"
        elif code == '47': return "La Haute-Yamaska"
        else: return None

    @staticmethod
    def getCEPByCode(code):
        """ Permet de retourner le nom du CEP selon le code inscrit dans IIT """
        code = str(code)
        if code == '104': return "Mégantic"
        elif code == '110': return "Saint-François"
        elif code == '116': return "Sherbrooke"
        elif code == '120': return "Orford"
        elif code == '126': return "Johnson"
        elif code == '132': return "Richmond"
        elif code == '204': return "Brome-Missisquoi"
        elif code == '206': return "Granby"
        elif code == '802': return "Beauce-Sud"
        else: return None
    
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