# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtGui import QPixmap, QIcon

def getIcon(icon_name, ext=".png"):
    plugin_dir = os.path.dirname(os.path.dirname(__file__))
    return QIcon(os.path.realpath(os.path.join(plugin_dir, f"icons/{icon_name}{ext}")))

def getPixmap(icon_name, ext=".png"):
    plugin_dir = os.path.dirname(os.path.dirname(__file__))
    return QPixmap(os.path.realpath(os.path.join(plugin_dir, f"icons/{icon_name}{ext}")))