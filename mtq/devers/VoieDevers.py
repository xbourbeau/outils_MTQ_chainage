from ..geomapping.LineRTSS import LineRTSS

from .Measurement import Measurement
from .Slope import Slope

class VoieDevers:

    def __init__(self, largeur, offset:float=0, side=1):
        # Attributs de la voie
        self._largeur = largeur
        self._offset = offset
        self._side = side

        # Largeur des bandes normées
        self.largeur_bande_2 = 0.75
        self.largeur_bande_3 = 1
        self.largeur_bande_4 = 0.75

        # Largeur restante de la voie pour les bandes variables
        largeur_restante = self.largeur() / (self.largeur_bande_3+self.largeur_bande_4+self.largeur_bande_2)
        # Largeur des bandes variables
        self.largeur_bande_1 = largeur_restante/2
        self.largeur_bande_5 = largeur_restante/2

        self.liste_mesurment_points = self.calculate_mesurement_points()
        self.liste_slopes:list[Slope] = []

    @classmethod
    def droite(cls, largeur, offset=0):
        """
        Créer un devers pour le côté droit
        
        Args:
            largeur (float): Width of the devers.
            offset (float): Offset from the center line.
            
        Returns:
            VoieDever: L'objet VoieDever
        """
        return cls(largeur, offset=offset, side=1)
    
    @classmethod
    def gauche(cls, largeur, offset=0):
        """
        Créer un devers pour le côté gauche
        
        Args:
            largeur (float): Width of the devers.
            offset (float): Offset from the center line.
            
        Returns:
            VoieDever: L'objet VoieDever
        """
        return cls(largeur, offset=offset, side=-1)

    @classmethod
    def from_line_rtss(cls, line_rtss:LineRTSS):
        largeur = abs(line_rtss.endOffset() - line_rtss.startOffset())

        if max([i.getOffset() for i in line_rtss], key=abs) >= 0: side = 1
        else: side = -1

        return cls(largeur, offset=min([i.getOffset() for i in line_rtss], key=abs), side=side)

    def __str__(self): return f"Voie {'gauche' if self.side() == -1 else 'droite'} de {self.largeur()} m"
    
    def __repr__(self): return self.__str__()
    
    def __len__(self):
        """
        Get the number of measurement points in the devers.
        
        Returns:
            int: Number of measurement points.
        """
        return len(self.liste_mesurment_points)

    def __iter__(self): 
        """
        Iterate over the measurement points.
        
        Returns:
            iterator: An iterator over the measurement points.
        """
        return iter(self.liste_mesurment_points)
    
    def __getitem__(self, idx): 
        try: return self.liste_mesurment_points[idx]
        except: raise IndexError(f"Index {idx} out of range for VoieDevers with {len(self)} measurement points.")

    def get_division_bande(self, add_offset=True):
        bandes = [self.bande_1(), 
                  self.bande_2(), 
                  self.bande_3(), 
                  self.bande_4(), 
                  self.bande_5()]
        if add_offset: 
            if self.side() == 1: bandes = [bande + self.offset() for bande in bandes]
            else: bandes = [self.offset() - bande for bande in bandes]
        return bandes

    def calculate_mesurement_points(self, add_offset=True):
        """
        Get measurement points along the devers
        
        Args:
            add_offset (bool): If True, adds the offset to the bande positions
            
        Returns:
            list: List of MesurementPoint objects
        """
        bandes = self.get_division_bande(add_offset=add_offset)
        mesuments_points = [Measurement("Centre", self.offset())]
        mesuments_points.extend([Measurement(f"Bande {i+1}", offset_bande) for i, offset_bande in enumerate(bandes)])
        mesuments_points.append(Measurement("Bord de voie", self.offset_largeur()))

        return mesuments_points

    def calculate_slopes(self):
        """
        Calculate slopes between consecutive measurement points.
        
        Returns:
            list: List of slopes (in percentage) between consecutive points.
                A positive slope means the road rises from left to right.
        """
        self.liste_slopes:list[Slope] = []
        
        for i in range(len(self) - 1):
            slope = Slope(i+1, self.mesurement_points()[i], self.mesurement_points()[i + 1])
            #if self.side() == -1: slope.reverse()
            self.liste_slopes.append(slope)

    def bande_1(self): 
        return self.largeur_bande_1/2

    def bande_2(self):
        return self.bande_3() - (self.largeur_bande_3/2) - (self.largeur_bande_2/2)

    def bande_3(self):
        return self.largeur() / 2
    
    def bande_4(self):
        return self.bande_3() + (self.largeur_bande_3/2) + (self.largeur_bande_2/2)
    
    def bande_5(self):
        return self.largeur() - (self.largeur_bande_5/2)

    def largeur(self): return self._largeur
    
    def mesurement_points(self): return self.liste_mesurment_points

    def center_mesurement_point(self): return self.liste_mesurment_points[0]

    def side(self): return self._side
    
    def slopes(self): return self.liste_slopes

    def offset(self): return self._offset

    def offset_largeur(self): return self.offset() + (self.largeur() * self.side())
