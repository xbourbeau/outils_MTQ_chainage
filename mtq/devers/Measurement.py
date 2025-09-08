from qgis.core import QgsPointXY, QgsGeometry
from typing import Union

class Measurement(QgsPointXY):

    def __init__(self, name, offset_bande, x=None, y=None, z=None):
        self._name = name
        self._offset_bande = offset_bande

        if x is None or y is None: super().__init__()
        else: super().__init__(x, y)

        self._z = z

    def __str__(self): return f"MesurementPoint(bande={self._name}, offset_bande={self._offset_bande}, z={self._z})"
    
    def __repr__(self): return self.__str__()

    def name(self): return self._name

    def offset_bande(self): return self._offset_bande

    def set_position(self, point_geom:Union[QgsGeometry, QgsPointXY]):
        """
        Set the position of the measurement point based on a QgsGeometry or QgsPointXY object.
        
        Args:
            point_geom (QgsGeometry/QgsPointXY): The point geometry to set the position.
        """
        if isinstance(point_geom, QgsPointXY): point = point_geom
        elif isinstance(point_geom, QgsGeometry): point =  point_geom.asPoint()
        else: raise TypeError("point_geom must be a QgsPointXY or QgsGeometry object.")
        
        self.setX(point.x())
        self.setY(point.y())

    def z(self):
        if self._z is None: raise ValueError("Z value is not set.")
        return self._z

    def set_z(self, z): self._z = z