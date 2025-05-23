# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
from qgis.core import QgsRaster, QgsFeature, QgsRasterLayer

class ProfilElevation:
    """
    Class pour representer une geometry lineaire sur une figure de type profil sur Mathplotlib.
    La geometry de la ligne doit être dans la même projection que le MNT
    """
    def __init__(self, name, geometry, id=None):
        """
        Méthode de création de l'objet
        
        Args:
            - name (str) = Nom de la ligne (permet de l'ajouter à la légende ou en annotation)
            - geometry (QgsGeometry) = Une geometry linéaire à représenter sur le profil
        """
        # Nom de la ligne
        self.name = name
        # Une geometry linéaire
        self.geometry = geometry
        # Identifiant unique pour la ligne
        self.id = id
        # Liste des X
        self.list_x = []
        # Liste des Y
        self.list_y = []

    @classmethod
    def fromFeat(cls, name:str, feat:QgsFeature, layer_mnt:QgsRasterLayer, interval=1, make_spline=True, smooth=False):
        """
        Permet de créer un objet ProfilElevation à partir d'un QgsFeature 

        Args:
            name (str): Nom de la ligne (permet de l'ajouter à la légende ou en annotation)
            feat (QgsFeature): L'entité à utiliser pour le profil
            layer_mnt (QgsRasterLayer): La couche du MNT à utiliser
            interval (int, optional): La distance le long de la ligne à utiliser pour identifier chaques Z. Defaults to 1.
            make_spline (bool, optional): Détermine si la ligne du profil doit être représenté en spline (Vrai/Faux). Defaults to True.
            smooth (bool, optional): Smooth profil. Defaults to False.

        Returns: l'objet ProfilElevation avec les élévation calculé
        """
        # Créer un instance de l'objet ProfilLine(nom, geometry)
        profil = cls(name, feat.geometry(), id=feat.id())
        # Indentifier les Z au mètre à partir du MNT et générer une spline
        profil.getElevationFromMNT(layer_mnt, interval=interval, make_spline=make_spline, smooth=smooth)
        return profil
    
    def getMinX(self):
        """ Permet de retourner la valeur minimum de l'axe des X du profil """
        return min(self.list_x)
    
    def getMinY(self):
        """ Permet de retourner la valeur minimum de l'axe des X du profil """
        return min(self.list_y)
    
    def getMaxX(self):
        """ Permet de retourner la valeur minimum de l'axe des X du profil """
        return max(self.list_x)
    
    def getMaxY(self):
        """ Permet de retourner la valeur minimum de l'axe des X du profil """
        return max(self.list_y)
    
    def drawProfil(self, ax, exageration_vertical=3, **kwargs):
        """
        Méthode qui permet de dessiner la ligne de profile sur un graphique Mathplotlib.
        
        Args:
            - ax (matplotlib.axes.Axes) = Axes object contaning all the elements of an individual (sub-)plot in a figure
            - exageration_vertical (int) = L'exagération vertical du graphique (par défault = 3)
            - **kwargs: (key:value) = Toute autre valeur de l'axe pouvant être modifier
        """
        ax.plot(self.list_x, self.list_y, label=self.name, **kwargs)
        ax.set_aspect(exageration_vertical)
    
    def getElevationFromMNT(self, layer_mnt, interval=1, make_spline=True, smooth=False):
        """
        Méthode qui permet de définir les X et les Y du profil selon un MNT
        et un interval de distance le long de la ligne. La ligne peux ensuite être représenter sous form de spline.
        La couche du MNT doit être dans la même projection que la géometrie de la ligne.
        Si le Z du MNT est NULL ou inexistant, le Z sera mis à 0.
        
        Entrée:
            - layer_mnt (QgsRasterLayer) = La couche raster du MNT à utiliser pour identifier les Z
            - interval (float/int) = La distance le long de la ligne à utiliser pour identifier chaques Z
            - make_spline (bool) = Détermine si la ligne du profil doit être représenté en spline (Vrai/Faux)
            - smooth (bool) = Smooth profil
        """
        # Parcourir chaque intreval de distance entre le début et la fin de la ligne
        for distance in np.arange(0, self.geometry.length(), interval):
            # Le QgsPointXY représentant la distance courante le long de la ligne
            point = self.geometry.interpolate(distance).asPoint()
            # Identifier la valeur du pixel du MNT en dessous du point
            mnt_z_value = layer_mnt.dataProvider().identify(point, QgsRaster.IdentifyFormatValue).results()[1]
            # Définir l'élévation à 0 si le Z est NULL
            if mnt_z_value is None: mnt_z_value = 0
            # Ajouter la distance courant à la liste des X
            self.list_x.append(distance)
            # Ajouter le Z à la liste des Y
            self.list_y.append(mnt_z_value)
        # Générer la spline avec les listes des X/Y si la ligne du profil doit être représenté en spline 
        if make_spline: self.generateSpline()
        # Smooth profile
        if smooth: self.smoothProfil()
    
    def smoothProfil(self, window_size=51, polynomial=3):
        self.list_y = savgol_filter(self.list_y, window_size, polynomial)
    
    def generateSpline(self):
        """ Méthode qui permet de générer une spline avec la liste des X et Y. """
        # Générer la spline à partir de la fonction de scipy et des liste X/Y
        spline = make_interp_spline(self.list_x, self.list_y)
        # Remplacer la liste des x par 100 fois plus de points pour interpoler la spline créer
        self.list_x = np.linspace(min(self.list_x), max(self.list_x), len(self.list_x)*100)
        # Interpoler la nouvelle liste des X sur la spline pour définir la liste des Y
        self.list_y = spline(self.list_x)

    def show(self, exageration_v=5, **kwargs):
        """
        Permet de visualiser le profil avec mathplotlib

        Args:
            exageration_v (int, optional): L'exagération vertical du profile. Defaults to 5.
        """
        # Créer un graphique 
        fig, ax = plt.subplots(1)
        # Reduire le padding autour du graphique
        plt.tight_layout(pad=2)
        # Définir les titre des axes
        plt.xlabel("Distance (m)")
        plt.ylabel("Élévation (m)")
        # Montrer les subdivision
        plt.minorticks_on()

        # Dessiner la ligne de profil sur l'axe du graphique avec une exagération vertical
        self.drawProfil(ax, exageration_vertical=exageration_v, **kwargs)
        ax.set_xbound(lower=self.getMinX(), upper=self.getMaxX())
        y_margins = (self.getMaxY() - self.getMinY()) * 0.05
        ax.set_ybound(lower=self.getMinY() - y_margins, upper=self.getMaxY() + y_margins)
        # Ajouter un text en bas à droite pour indiquer l'exagération vertical du graphique
        if exageration_v != 1: ax.annotate(f'Exagération vertical: {exageration_v}', (self.getMaxX()-0.2, self.getMinY()-y_margins+0.2), ha="right")

        plt.show()