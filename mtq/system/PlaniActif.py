# -*- coding: utf-8 -*-
from .SIGO import SIGO

class PlaniActif(SIGO):

    def __init__(self, default_url="https://planiactifs.transports.qc/tq/planiactifs/?context=_default"):
        
        super().__init__(default_url)