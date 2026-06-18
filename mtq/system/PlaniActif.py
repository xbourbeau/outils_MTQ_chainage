# -*- coding: utf-8 -*-
from .SIGO import SIGO

class PlaniActif(SIGO):

    def __init__(self, default_url="https://igo.mtq.min.intra/tq/sigo/?context=ga_chaussee"):
        
        super().__init__(default_url)