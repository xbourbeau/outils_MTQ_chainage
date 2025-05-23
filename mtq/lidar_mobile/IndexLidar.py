# Import général
import os
from datetime import datetime
# Import QGIS
from qgis.core import (QgsGeometry, QgsFeature, QgsPointXY, QgsVectorLayer,
    QgsCoordinateReferenceSystem, QgsPoint, QgsSpatialIndex)


# Import du module
from ..param import (
    DEFAULT_NOM_CHAMP_LIDAR_ID,
    DEFAULT_NOM_CHAMP_LIDAR_DATE,
    DEFAULT_NOM_CHAMP_LIDAR_TELECHARGEMENT)
from ..functions.downloadFile import downloadFile

class IndexLidar:
    """
    Un objet qui représent l'emplacement d'une ligne de téléchargement du LIDAR mobile
    sur le réseau du MTQ.
    """

    __slots__ = ("index_id", "index_date", "index_geometry", "index_crs", "lien_telechargement", "index_file")

    def __init__(
            self,
            id,
            date:datetime,
            geometry:QgsGeometry=None,
            crs:QgsCoordinateReferenceSystem=None,
            lien_telechargement:str=None,
            file:str=None):
        """
        Créer un objet IndexLidar pour la localisation d'un index lidar.

        Args:
            id (str): L'identifiant de l'index ex: (000375-011-0001)
            date (datetime): La date de relevée du LIDAR
            geometry (QgsGeometry, optional): La geometry de la ligne d'index. Defaults to None.
            lien_telechargement (str, optional): Le lien pour le téléchargement du fichier lidar. Defaults to None.
            file (str, optional): Le lien vers le fichier du lidar sur le poste. Defaults to None.
        """
        # Définir l'identifiant de l'index
        self.index_id = id
        # Définir la date du relevée
        self.index_date = date
        # Définir la géometry de la trajectoire de l'index
        self.index_geometry = geometry
        # Définir la projection de la géometry
        self.index_crs = crs
        # Défini le lien de téléchargement
        self.lien_telechargement = lien_telechargement
        # Définir le chemin vers le fichier (laz, las)
        self.index_file = self.getDefaultFile() if file is None else file

    @classmethod
    def fromFeat(cls, feat:QgsFeature, crs:QgsCoordinateReferenceSystem=None):
        """
        Permet de créer l'objet IndexLidar à partir du feature de la couche de la trajectoir du lidar mobile 

        Args:
            feat (QgsFeature): Le feature de la couche de la trajectoir du lidar mobile
            crs (QgsCoordinateReferenceSystem): Le système de coordonée de la géometry

        Returns: L'objet IndexLidar 
        """
        return cls(
            id=feat[DEFAULT_NOM_CHAMP_LIDAR_ID],
            date=datetime.strptime(feat[DEFAULT_NOM_CHAMP_LIDAR_DATE].toString("yyyy-MM-dd"), f"%Y-%m-%d"),
            geometry=feat.geometry(),
            crs=crs,
            lien_telechargement=feat[DEFAULT_NOM_CHAMP_LIDAR_TELECHARGEMENT])
    
    def __str__ (self): return self.name()
    
    def __repr__ (self): return f"IndexLidar {self.id()}: {self.name()}"

    def id(self): return self.index_id

    def name(self, suffix="", ext=".laz"):
        """
        Permet de retourner le nom de fichier lidar
        
        Args:
            suffix (str) = Un suffix a ajouter a la fin du nom
            ext (str) = L'extention du fichier
        """
        return f"{self.date(r'%Y%m%d')}_{self.id().replace('-', '_')}{suffix}{ext}"
    
    def file(self):
        """ Permet de retourner le chemin vers le fichier las ou laz du lidar """
        return self.index_file

    def folder(self):
        """ Permet de retourner le chemin vers le dossier qui contient le las ou laz du lidar """
        return os.path.dirname(self.file())

    def createFile(self, suffix:str):
        """ Permet de créer une nom de fichier avec un suffix """
        return os.path.join(self.folder(), self.name(suffix))

    def crs(self) : return self.index_crs

    def geometry(self) -> QgsGeometry: 
        return self.index_geometry

    def download(self, file=""):
        """ Permet de télégarger le fichier du lidar correspndant à l'index """
        if os.path.exists(os.path.dirname(file)): self.index_file = file
        if downloadFile(self.lien_telechargement, self.index_file): return True
        else: return False

    def date(self, format=r"%Y-%m-%d"):
        """ Permet de retourner la date du passage du lidar """
        if format: return self.index_date.strftime(format)
        else: return self.index_date

    def getTrajectoryCoords(self):
        """ Peremet de retourner la liste des coordonnées de la ligne de trajectoire """
        return [QgsPointXY(pts) for pts in self.geometry().vertices()]

    def getDefaultFile(self, folder=""):
        """ Permet de retourner le chemin de téléchargment du fichier laz par défault """
        if os.path.exists(folder): return os.path.join(folder, self.name())
        else: return os.path.expanduser("~") + f"\\Downloads\\{self.name()}"

    def year(self):
        """ Permet de retourner l'année de la prise du lidar """
        return self.date(None).year


    
