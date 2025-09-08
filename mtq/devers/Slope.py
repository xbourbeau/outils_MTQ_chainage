from qgis.core import QgsGeometry

from .Measurement import Measurement

class Slope:
    
    def __init__(self, idx,  point1: Measurement, point2: Measurement):
        self._idx = idx
        self.point1 = point1
        self.point2 = point2

        self.calculate()

    def calculate(self):
        """
        Calculate the slope between two measurement points.
        
        Returns:
            float: Slope in percentage.
        """
        distance = abs(self.point2.offset_bande() - self.point1.offset_bande())
        delta_z = self.point2.z() - self.point1.z()
        
        if distance > 0: self._slope = (delta_z / distance) * 100
        else: self._slope = None
    
    def index(self): return self._idx

    def name(self): return f"Slope {self.index()}"

    def slope(self): return self._slope

    def reverse(self): self._slope = self._slope * -1

    def as_geometry(self):
        """
        Get the geometry of the slope as a QgsGeometry object.
        
        Returns:
            QgsGeometry: Geometry representing the slope line.
        """
        return QgsGeometry.fromPolylineXY([self.point1, self.point2])

    def p1(self): return self.point1

    def p2(self): return self.point2