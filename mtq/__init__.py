"""
Module de base contenant des class et des fonctions pratique pour travailler avec des données du MTQ.
Entre autres: module de geocodage avec le système RTSS/chainage

Auteur: Xavier Bourbeau
Couriel: xavier.bourbeau@transport.gouv.qc.ca

"""

import sys
import os
# Get the current directory and add 'rapidfuzz' to the sys.path
extra_packages = os.path.join(os.path.dirname(__file__), 'packages')
if not extra_packages in sys.path: sys.path.append(extra_packages)

__all__ = ["core"]