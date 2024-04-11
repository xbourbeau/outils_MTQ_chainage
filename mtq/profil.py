import numpy as np
from scipy.interpolate import interp1d, make_interp_spline
from scipy.signal import savgol_filter

from qgis.core import QgsRaster

'''
Class pour representer une geometry lineaire sur une figure de type profil sur Mathplotlib.
La geometry de la ligne doit être dans la même projection que le MNT
'''
class ProfileLine():
    
    '''
    Méthode de création de l'objet
       
    Entrée:
        - name (str) = Nom de la ligne (permet de l'ajouter à la légende ou en annotation)
        - geometry (QgsGeometry) = Une geometry linéaire à représenter sur le profil
    '''
    def __init__(self, name, geometry):
        # Nom de la ligne
        self.name = name
        # Une geometry linéaire
        self.geometry = geometry
        # Liste des X
        self.list_x = []
        # Liste des Y
        self.list_y = []
    
    '''
    Méthode qui permet de dessiner la ligne de profile sur un graphique Mathplotlib.
    
    Entrée:
        - ax (matplotlib.axes.Axes) = Axes object contaning all the elements of an individual (sub-)plot in a figure
        - exageration_vertical (int) = L'exagération vertical du graphique (par défault = 3)
        - **kwargs: (key:value) = Toute autre valeur de l'axe pouvant être modifier
    '''
    def drawProfil(self, ax, exageration_vertical=3, **kwargs):
        ax.plot(self.list_x, self.list_y, label=self.name, **kwargs)
        ax.set_aspect(exageration_vertical)
    
    '''
    Méthode qui permet de définir les X et les Y du profil selon un MNT
    et un interval de distance le long de la ligne. La ligne peux ensuite être représenter sous form de spline.
    La couche du MNT doit être dans la même projection que la géometrie de la ligne.
    
    Entrée:
        - layer_mnt (QgsRasterLayer) = La couche raster du MNT à utiliser pour identifier les Z
        - interval (float/int) = La distance le long de la ligne à utiliser pour identifier chaques Z
        - make_spline (bool) = Détermine si la ligne du profil doit être représenté en spline (Vrai/Faux)
        - smooth (bool) = Smooth profil
    '''
    def getElevationFromMNT(self, layer_mnt, interval=1, make_spline=True, smooth=False):
        # Parcourir chaque intreval de distance entre le début et la fin de la ligne
        for i, distance in enumerate(np.arange(0, self.geometry.length(), interval)):
            # Le QgsPointXY représentant la distance courante le long de la ligne
            point = self.geometry.interpolate(distance).asPoint()
            # Identifier la valeur du pixel du MNT en dessous du point
            mnt_z_value = layer_mnt.dataProvider().identify(point, QgsRaster.IdentifyFormatValue).results()[1]
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
    
    ''' Méthode qui permet de générer une spline avec la liste des X et Y. '''
    def generateSpline(self):
        # Générer la spline à partir de la fonction de scipy et des liste X/Y
        spline = make_interp_spline(self.list_x, self.list_y)
        # Remplacer la liste des x par 100 fois plus de points pour interpoler la spline créer
        self.list_x = np.linspace(min(self.list_x), max(self.list_x), len(self.list_x)*100)
        # Interpoler la nouvelle liste des X sur la spline pour définir la liste des Y
        self.list_y = spline(self.list_x)