from ...geomapping.Chainage import Chainage
from ...geomapping.RTSS import RTSS

class LocalisationSVN:
    
    def __init__(self, *, x=None, y=None, epsg=None, rtss:RTSS=None, chainage:Chainage=None):
        """ Initialise une localisation soit par coordonnées, soit par RTSS + chaînage. """
        # Définir la liste des epsg géréer par SVN360
        self.list_epsg_possible = ["4326", "3799", "4617"]

        if x is not None and y is not None and epsg is not None:
            self._mode = "coordinates"
            self._x = float(x)
            self._y = float(y)
            if str(epsg) not in self.list_epsg_possible: raise ValueError(f"EPSG {epsg} non supporté par SVN360.")
            self._epsg = int(epsg)
            self._rtss, self._chainage = None, None

        elif rtss is not None and chainage is not None:
            self._mode = "rtss"
            self._rtss = RTSS(rtss)
            self._chainage = Chainage(chainage)

            self._x, self._y, self._epsg = None, None, None
        else: raise ValueError("Tu dois fournir soit (x, y, epsg) soit (rtss, chainage)")

    @classmethod
    def from_rtss(cls, rtss:RTSS, chainage:Chainage):
        return cls(
            rtss=rtss,
            chainage=chainage,
            x=None,
            y=None,
            epsg=None)
    
    @classmethod
    def from_coords(cls, x, y, epsg):
        return cls(
            x=float(x),
            y=float(y),
            epsg=int(epsg),
            rtss=None,
            chainage=None)

    def __repr__(self):
        if self.mode == "coordinates": return f"LocalisationSVN(x={self.x}, y={self.y}, epsg={self.epsg})"
        else: return f"LocalisationSVN({self.rtss}', {self.chainage})"

    def mode(self): return self._mode

    def rtss(self): return self._rtss.valueFormater()

    def chainage(self): return self._chainage.value(precision=0)

    def x(self): return self._x

    def y(self): return self._y

    def epsg(self): return self._epsg

    def url_params(self):
        """ Retourne les paramètres URL selon le mode de la localisation. """
        if self.mode() == "rtss": return f"rtss={self.rtss()}&chainage={self.chainage()}"
        else: return f"x={self.x()}&y={self.y()}&Epsg={self.epsg()}"
