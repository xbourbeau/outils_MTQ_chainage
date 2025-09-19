# -*- coding: utf-8 -*-
import os
from qgis.core import QgsMapLayerProxyModel, QgsFieldProxyModel

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import pyqtSignal

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'fenetre_selection_couche.ui'))

class fenetreSelectionCouche(QDialog, FORM_CLASS):

    closing_window = pyqtSignal()

    def __init__(self, layer_rtss_name, field_rtss_name, field_chainage_f_name, field_chainage_d_name, field_class_name, parent=None):
        self.layer_rtss_name = layer_rtss_name
        self.field_rtss_name = field_rtss_name
        self.field_chainage_f_name = field_chainage_f_name
        self.field_chainage_d_name = field_chainage_d_name
        self.field_class_name = field_class_name

        super(fenetreSelectionCouche, self).__init__(parent)
        self.setupUi(self)

        self.cbx_layer_rtss.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.cbx_field_rtss.setFilters(QgsFieldProxyModel.String)
        self.cbx_field_chainage_d.setFilters(QgsFieldProxyModel.String|QgsFieldProxyModel.Numeric)
        self.cbx_field_chainage.setFilters(QgsFieldProxyModel.String|QgsFieldProxyModel.Numeric)
        self.cbx_field_class.setFilters(QgsFieldProxyModel.String)
        
        # Set Layer comboBox 
        idx = self.cbx_layer_rtss.findText(self.layer_rtss_name)
        if idx != -1: self.cbx_layer_rtss.setCurrentIndex(idx)
        self.update_fields_comboboxs(self.cbx_layer_rtss.currentLayer())

        self.cbx_layer_rtss.layerChanged.connect(self.update_fields_comboboxs)

    def closeEvent(self, event):
        if self.isVisible():
            self.closing_window.emit()
            event.accept()

    def update_fields_comboboxs(self, layer):
        self.cbx_field_rtss.setLayer(layer)
        self.cbx_field_rtss.setField(self.field_rtss_name)

        self.cbx_field_chainage.setLayer(layer)
        self.cbx_field_chainage.setField(self.field_chainage_f_name)

        self.cbx_field_chainage_d.setLayer(layer)
        self.cbx_field_chainage_d.setField(self.field_chainage_d_name)

        self.cbx_field_class.setLayer(layer)
        self.cbx_field_class.setField(self.field_class_name)
