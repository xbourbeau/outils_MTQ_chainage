# -*- coding: utf-8 -*-
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import QLineEdit, QLabel, QCheckBox

class ToolbarWidjet:

    def __init__(self) -> None:
        pass
    
    @staticmethod
    def createLableFont()->QFont:
        """ Permet de créer le QFont pour les lables du Toolbar """
        # QFont for lables
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        return font
    
    @staticmethod
    def createLineEditFont()->QFont:
        """ Permet de créer le QFont pour les line edit du Toolbar """
        # QFont for lineedits
        font = QFont()
        font.setPointSize(9)
        return font
    
    @staticmethod
    def createLineEdit(read_only=False)->QLineEdit:
        """ Permet de créer le QLineEdit pour le Toolbar """
        line_edit = QLineEdit()
        line_edit.mousePressEvent = lambda _ : line_edit.selectAll()
        line_edit.setFrame(False)
        line_edit.setReadOnly(read_only)
        return line_edit
    
    @staticmethod
    def createLable(text:str)->QLabel:
        """ Permet de créer le QLabel pour le Toolbar """
        lable = QLabel()
        lable.setText(text)
        return lable