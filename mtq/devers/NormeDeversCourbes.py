import os
import pandas as pd

class NormeDeversCourbes:

    def __init__(self, tableau_excel):
        # Mettre à jour le tableau à partir du excel
        self.update_data_from_excel(tableau_excel)


    def update_data_from_excel(self, tableau_excel:str):
        if not os.path.exists(tableau_excel) or not ".xlsx" in tableau_excel: return
        # Stocker le chemin vers le Excel utiliser
        self.ref_tableau_excel = tableau_excel
        # Lire le Excel dans un DataFrame
        self.data = pd.read_excel(
            self.ref_tableau_excel,
            sheet_name="Data")
        # Définir les index du dataframe à partir de la combination des 2 inputs
        self.data.set_index(["rayon", "vitesse"], inplace=True, append=False, drop=True)

    def get_devers_courbe(self, rayon, vitesse):
        return self.data.loc[(rayon, vitesse), "e_courbe"]
    
    def get_devers_spirale(self, rayon, vitesse):
        return self.data.loc[(rayon, vitesse), "e_spirale"]
    
    def get_longueur_courbe(self, rayon, vitesse, voie=1):
        if voie == 1: return self.data.loc[(rayon, vitesse), "l2"]
        return self.data.loc[(rayon, vitesse), "l3-4"]
    
    def get_param_spirale(self, rayon, vitesse, voie=1):
        if voie == 1: return self.data.loc[(rayon, vitesse), "a2"]
        return self.data.loc[(rayon, vitesse), "a3-4"]
    
    def get_info(self, rayon, vitesse, is_spirale=False, voie=1):
        if is_spirale: return (self.get_devers_spirale(rayon, vitesse), self.get_param_spirale(rayon, vitesse, voie=voie))
        return (self.get_devers_courbe(rayon, vitesse), self.get_longueur_courbe(rayon, vitesse, voie=voie))