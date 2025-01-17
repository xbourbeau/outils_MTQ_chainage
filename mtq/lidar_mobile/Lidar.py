import os
import numpy as np
from shapely.geometry import box
from scipy.interpolate import interp1d

try: 
    import processing
    PROCESSSING_LIB = True
except: PROCESSSING_LIB = False

try: 
    from scipy.spatial import cKDTree
    SCIPY_LIB = True
except: SCIPY_LIB = False

from qgis.core import QgsGeometry, QgsCoordinateReferenceSystem, QgsVectorLayer
from .IndexLidar import IndexLidar

try: 
    import laspy
    LASPY_LIB = True
except: LASPY_LIB = False

class Lidar:
    """ Un objet Lidar qui représente un fichier .las ou .laz qui contient un nuage de point """

    def __init__(self, file_path:str):
        self.setPath(file_path)

    @classmethod
    def fromIndex(cls, index:IndexLidar):
        return cls(index.file())

    def __str__ (self): return f"Lidar: {self.file()}"
    
    def __repr__ (self): return f"Lidar: {self.file()}"

    def isValid(self, update=False):
        if update: self.checkIsValide()
        return self.is_valide

    def checkIsValide(self):
        try:
            laspy.read(self.file_path)
            self.is_valide = os.path.exists(self.file_path)
        except: self.is_valide = False

    def setPath(self, file_path:str):
        self.file_path = file_path
        self.checkIsValide()
        return self.is_valide
    
    def file(self): return self.file_path

    def crs(self):
        if not self.isValid(): return None
        with laspy.open(self.file()) as las_file:
            header = las_file.header
            crs = QgsCoordinateReferenceSystem()
            crs.createFromWkt(header.parse_crs().to_wkt())
            # Access the Coordinate Reference System (CRS)
            return crs

    def clip(self, output, clipping_layer:QgsVectorLayer, expression=None):
        params = {
            'INPUT': self.file(),
            'OVERLAY': clipping_layer,
            'FILTER_EXPRESSION': expression,
            'FILTER_EXTENT': None,
            'OUTPUT': output}
        res = processing.run("pdal:clip", params)
        return Lidar(res["OUTPUT"])
    
    def generateMNT(self, output, pixel_size=0.1):
        params = {
            'INPUT':self.file(),
            'RESOLUTION':pixel_size,
            'TILE_SIZE':1000,
            'FILTER_EXPRESSION':'Classification = 2',
            'FILTER_EXTENT':None,
            'ORIGIN_X':None,
            'ORIGIN_Y':None,
            'OUTPUT': output}
        processing.run("pdal:exportrastertin", params)

    def extent(self):
        if not self.isValid(): return None
        with laspy.open(self.file()) as las_file:
            header = las_file.header
            return  QgsGeometry().fromWkt(box(header.mins[0], header.mins[1], header.maxs[0], header.maxs[1]).wkt)

    def getPoints(self, **kwargs):
        """
        Filtre les points LiDAR en fonction de plusieurs paramètres et écrit les points filtrés dans un nouveau fichier.
    
        Args: 
            z_min (float) = Valeur minimale de z pour filtrer les points.
            z_max (float) = Valeur maximale de z pour filtrer les points.
            classifications (int/list) = Valeur de classification des points de sol à éliminer.
            intensity_min (float) = Valeur minimale de l'intensité pour filtrer les points.
            intensity_max (float) = Valeur maximale de l'intensité pour filtrer les points.
            x_min (float) = Valeur minimale de X pour filtrer les points.
            x_max (float) = Valeur maximale de X pour filtrer les points.
            y_min (float) = Valeur minimale de Y pour filtrer les points.
            y_max (float) = Valeur maximale de Y pour filtrer les points.
        
        Return: Numpy array of the points 
        """
        # Lecture du fichier LiDAR d'entrée
        las = laspy.read(self.file())
        mask = np.ones(len(las.x), dtype=bool)

        for arg_name, val in kwargs.items():
            if arg_name == "z_min": mask &= (las.z >= val)
            elif arg_name == "z_max": mask &= (las.z <= val)

            elif arg_name == "x_min": mask &= (las.x >= val)
            elif arg_name == "x_max": mask &= (las.x <= val)

            elif arg_name == "y_min": mask &= (las.y >= val)
            elif arg_name == "y_max": mask &= (las.y <= val)

            elif arg_name == "intensity_min": mask &= (las.intensity >= val)
            elif arg_name == "intensity_max": mask &= (las.intensity <= val)

            elif arg_name == "classifications": 
                if not isinstance(val, list): val = [val]
                mask &= np.isin(las.classification, val)
        
        return las.points[mask]

    def fitLine(self, points, search_distance:float=1, **kwargs):
        # Samples les valeurs d'élévation au sol des points de trajectoire
        z = self.sampleElevations(points, search_distance, **kwargs)
        # Ajouter les Z au coordonnées de trajectoire 
        points_z = np.hstack((points, np.array([[i] for i in z])))
        # Retirer les points avec une élévation Null (extrémitée) 
        return points_z[~np.isnan(points_z).any(axis=1)]

    def exagerationVertical(self, output, exageration=5):
        # Load the .laz file
        point_cloud = laspy.read(self.file())
        
        z = point_cloud.z

        new_z = z*exageration

        # Create a new point cloud with the modified Z values
        new_point_cloud = point_cloud
        # Update the Z values for the filtered points
        new_point_cloud.z = new_z
        # Save the modified point cloud to a new .laz file
        new_point_cloud.write(output)

        return Lidar(output)
    
    def interpolatePoints(self, points, points_per_m):
        """
        Interpolate points along a 3D polyline defined by multiple points.
        
        Parameters:
        points: array-like, shape (N, 3) - List of points defining the polyline [(x1,y1,z1), (x2,y2,z2), ...]
        points_per_m: int - Number of points to generate per meters (including endpoints)
        
        Returns:
        numpy.ndarray: Array containing the interpolated points for the entire polyline
        """
        # Convert input points to numpy array
        points = np.array(points)
        # Check if we have at least 2 points
        if len(points) < 2: raise ValueError("At least 2 points are required to define a polyline")
        # Initialize list to store interpolated points
        interpolated_segments = []
        # Process each segment
        for i in range(len(points) - 1):
            start, end = points[i], points[i + 1]
            distance = np.sqrt(np.sum((start - end) ** 2))
            # Create parameter t from 0 to 1
            t = np.linspace(0, 1, points_per_m*distance)
            # Interpolate each dimension
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            z = start[2] + (end[2] - start[2]) * t
            # Stack coordinates into a single array
            segment_points = np.column_stack((x, y, z))
            # For all segments except the last one, exclude the last point
            # to avoid duplicates at segment joints
            if i < len(points) - 2: segment_points = segment_points[:-1]
            interpolated_segments.append(segment_points)
        
        # Combine all segments
        return np.vstack(interpolated_segments)

    def applatir(self, output, line_coords):
        # Load the .laz file
        point_cloud = laspy.read(self.file())
        
        x = point_cloud.x
        y = point_cloud.y
        z = point_cloud.z
        
        # Sample points along the line
        sampled_points = np.asarray(line_coords)
        # Create a KD-Tree for efficient nearest neighbor search
        kdtree = cKDTree(sampled_points)
        
        # For each filtered point in the point cloud, find the closest sampled point on the line
        distances, indices = kdtree.query(np.column_stack((x, y, z)))
        # Subtract the interpolated Z values from the filtered point cloud Z values
        new_z = z - sampled_points[indices, 2]
        
        # Create a new point cloud with the modified Z values
        new_point_cloud = point_cloud
        # Update the Z values for the filtered points
        new_point_cloud.z = new_z
        # Save the modified point cloud to a new .laz file
        new_point_cloud.write(output)

        return Lidar(output)

    def sampleElevation(self, coord, search_distance:float=1, **kwargs):
        """
        Permet de trouver la valeur moyenne des élévations du nuage autour d'un point

        Args:
            coord (tuple): Les coordonnées X et Y du point à utiliser pour l'échantillonage
            search_distance (float): Distance de recherche autour du point
        
        kwargs (pour filtrer):
            z_min (float) = Valeur minimale de z pour filtrer les points.
            z_max (float) = Valeur maximale de z pour filtrer les points.
            classifications (int/list) = Valeur de classification des points de sol à éliminer.
            intensity_min (float) = Valeur minimale de l'intensité pour filtrer les points.
            intensity_max (float) = Valeur maximale de l'intensité pour filtrer les points.
            x_min (float) = Valeur minimale de X pour filtrer les points.
            x_max (float) = Valeur maximale de X pour filtrer les points.
            y_min (float) = Valeur minimale de Y pour filtrer les points.
            y_max (float) = Valeur maximale de Y pour filtrer les points.

        Returns: L'élévation (Z) moyenne du nuage autour du point
        """
        # Load the .laz file
        point_cloud = self.getPoints(**kwargs)
        # Extract X, Y, Z coordinates from the point cloud
        x = point_cloud.x
        y = point_cloud.y
        z = point_cloud.z
        # Combine the X, Y (and optionally Z) coordinates into an array for the KD-Tree
        points = np.column_stack((x, y))
        # Build the cKDTree
        tree = cKDTree(points)
        # Query the tree to find all points within the search distance of the input point
        indices = tree.query_ball_point(coord, search_distance)
        
        # Use the indices to filter the points
        return np.mean(z[indices])
    
    def sampleElevations(self, coords:list, search_distance:float=1, **kwargs):
        """
        Permet de trouver la valeur moyenne des élévations du nuage autour
        de chaque point d'une liste

        Args:
            coord (list): List des coordonnées X et Y du point à utiliser pour l'échantillonage
            search_distance (float): Distance de recherche autour du point
        
        kwargs (pour filtrer):
            z_min (float) = Valeur minimale de z pour filtrer les points.
            z_max (float) = Valeur maximale de z pour filtrer les points.
            classifications (int/list) = Valeur de classification des points de sol à éliminer.
            intensity_min (float) = Valeur minimale de l'intensité pour filtrer les points.
            intensity_max (float) = Valeur maximale de l'intensité pour filtrer les points.
            x_min (float) = Valeur minimale de X pour filtrer les points.
            x_max (float) = Valeur maximale de X pour filtrer les points.
            y_min (float) = Valeur minimale de Y pour filtrer les points.
            y_max (float) = Valeur maximale de Y pour filtrer les points.

        Returns: La liste des élévation (Z) moyenne du nuage autour de chaque point
        """
        # Load the .laz file
        point_cloud = self.getPoints(**kwargs)
        # Extract X, Y, Z coordinates from the point cloud
        x = point_cloud.x
        y = point_cloud.y
        z = point_cloud.z
        # Combine the X, Y (and optionally Z) coordinates into an array for the KD-Tree
        points = np.column_stack((x, y))
        # Build the cKDTree
        tree = cKDTree(points)
        elevations = []
        for coord in coords:
            # Query the tree to find all points within the search distance of the input point
            indices = tree.query_ball_point(coord, search_distance)
            elevations.append(np.mean(z[indices]))
        # Use the indices to filter the points
        return elevations

