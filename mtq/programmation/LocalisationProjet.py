# -*- coding: utf-8 -*-

from pandas import Series

from ..geomapping.LineRTSS import LineRTSS
from ..geomapping.RTSS import RTSS
from ..geomapping.Chainage import Chainage
from ..geomapping.PointRTSS import PointRTSS


class LocalisationProjet(LineRTSS):

    def __init__(
            self,
            id:int,
            rtss:RTSS,
            chainage_d:Chainage,
            chainage_f:Chainage,
            description:str=None,
            id_structure=None):
        
        self._id = id
        self._desc = description
        self._id_structure = id_structure
        super().__init__([PointRTSS(rtss, chainage_d), PointRTSS(rtss, chainage_f)], interpolate_on_rtss=True)

    @classmethod
    def from_pps_access(cls, t_loc_carto:Series):
        rtss = t_loc_carto.get("NUM_RTS_REFRN")
        cd = t_loc_carto.get("VAL_CHANG_PROJT_DEBUT")
        cf = t_loc_carto.get("VAL_CHANG_PROJT_FIN")
        id = t_loc_carto.get("IDE_LOCLS_ROUTR_PROJT")
        description = t_loc_carto.get("DES_LOCLS")
        id_structure = t_loc_carto.get("NUM_DOSSR_STRCT")        

        return cls(id, rtss, cd, cf, description, id_structure)
    
    def id(self): return self._id