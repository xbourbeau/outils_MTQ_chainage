# -*- coding: utf-8 -*-
import os

from qgis.core import QgsMapLayerProxyModel, QgsFieldProxyModel, QgsProject
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon, QKeySequence, QColor
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal

# Class pour la gestion des paramètre du plugin
from ..modules.PluginParametres import PluginParametres
from ..functions.checkIfKeySequenceExists import checkIfKeySequenceExists
from .fenetre_selection_couche import fenetreSelectionCouche

from ..mtq.fnt import choisirFichier
from ..mtq.utils import Utilitaire

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'fenetre_parametre.ui'))
    
class fenetreParametre(QDialog, FORM_CLASS):

    closing_window = pyqtSignal()
    plugin_inactif = pyqtSignal()
    plugin_actif = pyqtSignal()
    generate_index = pyqtSignal()
    delete_index = pyqtSignal()
    parametre_updated = pyqtSignal()


    def __init__(self, iface:QgisInterface, parent=None):
        """Constructor."""
        self.iface = iface
        super(fenetreParametre, self).__init__(parent)
        self.setupUi(self)
        
        # Class de gestion des paramètres
        self.params = PluginParametres()

        self.widgets_action = {
            "Suivre le chainage": self.chx_follow_chainage,
            "Mesurer un chainage": self.chx_distance,
            "Calculer un interval de chainage": self.chx_interval_chainage,
            "Calculer des transects": self.chx_transects,
            "Calculer des atlas": self.chx_atlas,
            "Placer des écussons": self.chx_ecussons,
            "Creation de geometrie": self.chx_create_geometrie,
            "Geocodage inverse": self.chx_geocoder_inverse,
            "Open SIGO": self.chx_open_sigo,
            "Open SVN": self.chx_open_svn,
            "Open SVN 360": self.chx_open_svn_360}
        
        self.checkbox_tooltip = {
            "show_rtss_on_map": self.chx_tooltip_rtss,
            "show_chainage_on_map": self.chx_tooltip_chainage,
            "show_distance_on_map": self.chx_tooltip_offset,
            "show_context_on_map": self.chx_tooltip_context}
        
        # Définir les raccourcis clavier
        self.raccourci = {
            "raccourcis_clavier_parralele": {"chx": self.chk_shorcut_parallele, "key": self.key_shortcut_parallele},
            "raccourcis_clavier_perpendiculaire": {"chx": self.chk_shorcut_perpendiculaire, "key": self.key_shortcut_perpendiculaire},
            "raccourcis_clavier_interpolate_rtss": {"chx": self.chk_shorcut_interpolate, "key": self.key_shortcut_interpolate}
        }
        
        self.cbx_layer_context.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.cbx_field_route.setFilters(QgsFieldProxyModel.String|QgsFieldProxyModel.Numeric)
        self.cbx_field_value.setFilters(QgsFieldProxyModel.String|QgsFieldProxyModel.Numeric)

        # Connections
        self.btn_enregistrer.clicked.connect(self.saveSettings)
        self.btn_annuler.clicked.connect(self.initialisePresentValues)
        self.btn_set_default_values.clicked.connect(self.initialiseAllDefaultValues)
        self.btn_generate_index.clicked.connect(self.generateContextLayerIndex)
        self.btn_delete_index.clicked.connect(lambda: self.delete_index.emit())
        self.btn_selectionner_layer_rtss.clicked.connect(self.selectionnerCoucheRTSS)
        self.btn_geocatalogue.clicked.connect(lambda: os.startfile("http://geocatalogue.mtq.qc/geonetwork/srv/fre/catalog.search#/metadata/180589bb-ccfa-464c-95ad-2b620c62e398"))

        self.btn_symblologie_ecusson.clicked.connect(lambda: self.choisirQML(self.txt_sybologie_ecusson))
        self.btn_symblologie_chainage.clicked.connect(lambda: self.choisirQML(self.txt_sybologie_chainage))
        self.btn_symblologie_transect.clicked.connect(lambda: self.choisirQML(self.txt_sybologie_transect))
        self.btn_symblologie_atlas.clicked.connect(lambda: self.choisirQML(self.txt_sybologie_atlas))

        self.cbx_layer_context.layerChanged.connect(self.setLayerContextCombobox)

        self.key_shortcut.keySequenceChanged.connect(self.checkKeyShortcutChainage)
        self.key_shortcut_ecusson.keySequenceChanged.connect(self.checkKeyShortcutEcusson)
        self.key_shortcut_distance.keySequenceChanged.connect(self.checkKeyShortcutDistance)
        set_seq_length = lambda k: self.key_shortcut_parallele.setKeySequence(QKeySequence(k.toString().split(", ")[0]))
        self.key_shortcut_parallele.keySequenceChanged.connect(set_seq_length)
        set_seq_length = lambda k: self.key_shortcut_perpendiculaire.setKeySequence(QKeySequence(k.toString().split(", ")[0]))
        self.key_shortcut_perpendiculaire.keySequenceChanged.connect(set_seq_length)
        set_seq_length = lambda k: self.key_shortcut_interpolate.setKeySequence(QKeySequence(k.toString().split(", ")[0]))
        self.key_shortcut_interpolate.keySequenceChanged.connect(set_seq_length)

        # Définir les image des tabs
        self.setTabsIcons()
        
        # Définir l'icon des boutons pour choisir le fichier de symbologie
        qml_icon = self.params.getIcon("qml")
        symbologie_buttons = [self.btn_symblologie_chainage, self.btn_symblologie_ecusson, self.btn_symblologie_transect, self.btn_symblologie_atlas]
        for btn in symbologie_buttons: btn.setIcon(qml_icon)
        
        self.rbt_planiactif.setIcon(self.params.getIcon("igo"))
        self.rbt_sigo.setIcon(self.params.getIcon("igo"))
        self.btn_enregistrer.setIcon(self.params.getIcon("save"))
        self.btn_geocatalogue.setIcon(self.params.getIcon("geocatalogue"))

        # Définir l'icon du checkbox pour montrer le marqueur de direction du RTSS
        self.chx_marqueur_dir.setIcon(self.params.getIcon("marker_dir"))

        # Parcourir les widget de case a cocher et définir son état et l'icon de l'action associé
        for action_name, widget in self.widgets_action.items():
            # Action associé au widjet
            action = self.params.getAction(action_name)
            # Définir son icon
            if action: widget.setIcon(QIcon(action.getIcon()))

    def setInterfaceActive(self):
        if self.isVisible(): self.raise_()
        else: 
            self.initialisePresentValues()
            self.plugin_inactif.emit()
            # Set the current tab to be the first
            self.tabWidget.setCurrentIndex(0)
            self.show()

    def closeEvent(self, event):
        if self.isVisible():
            self.closing_window.emit()
            self.plugin_actif.emit()
            event.accept()
    
    def setTabsIcons(self):
        # Définir les image des tabs
        self.tabWidget.setTabIcon(0, self.params.getIcon("parametres"))
        self.tabWidget.setTabIcon(1, self.params.getRotatatedIcon("chaine", 90))
        self.tabWidget.setTabIcon(2, self.params.getRotatatedIcon("chainage", 90))
        self.tabWidget.setTabIcon(3, self.params.getRotatatedIcon("mesure", 90))
        self.tabWidget.setTabIcon(4, self.params.getRotatatedIcon("ecusson", 90))
        self.tabWidget.setTabIcon(5, self.params.getRotatatedIcon("create_line", 90))
        self.tabWidget.setTabIcon(6, self.params.getRotatatedIcon("geocodage_inverse", 90))
        self.tabWidget.setTabIcon(7, self.params.getRotatatedIcon("context_layer", 90))
        self.tabWidget.setTabIcon(8, self.params.getRotatatedIcon("file", 90))

    def setLayerContextCombobox(self, layer):
        for cbx, param in ((self.cbx_field_route, "field_context_route"),
                            (self.cbx_field_value, "field_context_value")):
            cbx.setLayer(layer)
            idx = cbx.findText(self.params.getValue(param))
            if idx != -1: cbx.setCurrentIndex(idx)
    
    def initialisePresentValues(self, as_default=False):
        # Initialisé les valeurs selon les paramètres du plugin
        idx = self.cbx_layer_context.findText(self.params.getValue("context_layer", defaut=as_default))
        if idx != -1: self.cbx_layer_context.setCurrentIndex(idx)
        self.setLayerContextCombobox(self.cbx_layer_context.currentLayer())

        self.txt_layer_rtss.setText(self.params.getValue("layer_rtss", defaut=as_default))
        self.txt_field_rtss.setText(self.params.getValue("field_num_rtss", defaut=as_default))
        self.txt_field_chainage_fin.setText(self.params.getValue("field_chainage_fin", defaut=as_default))
        self.txt_field_chainage_debut.setText(self.params.getValue("field_chainage_debut", defaut=as_default))
        self.txt_field_class.setText(self.params.getValue("field_classification", defaut=as_default))

        self.chx_add_expressions.setChecked(self.params.getValue("load_custom_expressions", defaut=as_default))
        self.chx_format_rtss.setChecked(self.params.getValue("formater_rtss", defaut=as_default))
        self.chx_format_chainage.setChecked(self.params.getValue("formater_chainage", defaut=as_default))
        self.chx_marqueur_dir.setChecked(self.params.getValue("show_marker_direction", defaut=as_default))
        self.chk_copie_info_rtss.setChecked(self.params.getValue("show_copie_menu_info", defaut=as_default))
        self.chk_copie_formater.setChecked(self.params.getValue("show_copie_menu_formater", defaut=as_default))
        self.chk_copie_non_formater.setChecked(self.params.getValue("show_copie_menu_non_formater", defaut=as_default))
        self.chx_use_visible.setChecked(self.params.getValue("use_only_on_visible", defaut=as_default))
        self.spx_precision.setValue(self.params.getValue("precision_chainage", defaut=as_default))
        self.spx_precision_mesure.setValue(self.params.getValue("precision_mesure", defaut=as_default))
        self.spx_precision_dist.setValue(self.params.getValue("precision_distance", defaut=as_default))
        self.txt_layer_ecusson.setText(self.params.getValue("layer_ecusson_name", defaut=as_default))
        self.txt_champ_route.setText(self.params.getValue("layer_ecusson_field_route", defaut=as_default))
        self.txt_champ_classe.setText(self.params.getValue("layer_ecusson_field_classe", defaut=as_default))
        self.txt_sybologie_ecusson.setText(self.params.getValue("layer_ecusson_style", defaut=as_default))
        self.txt_sybologie_chainage.setText(self.params.getValue("layer_chainage_style", defaut=as_default))
        self.txt_sybologie_transect.setText(self.params.getValue("layer_transect_style", defaut=as_default))
        self.txt_sybologie_atlas.setText(self.params.getValue("layer_atlas_style", defaut=as_default))
        self.chk_shorcut_chainage.setChecked(self.params.getValue("use_raccourcis_chainage", defaut=as_default))
        self.key_shortcut.setKeySequence(QKeySequence(self.params.getValue("raccourcis_clavier", defaut=as_default)))
        self.chk_shorcut_ecusson.setChecked(self.params.getValue("use_raccourcis_ecusson", defaut=as_default))
        self.key_shortcut_ecusson.setKeySequence(QKeySequence(self.params.getValue("raccourcis_clavier_ecusson", defaut=as_default)))
        self.chk_shorcut_distance.setChecked(self.params.getValue("use_raccourcis_distance", defaut=as_default))
        self.key_shortcut_distance.setKeySequence(QKeySequence(self.params.getValue("raccourcis_clavier_distance", defaut=as_default)))
        self.mFontButton.setCurrentFont(self.params.getValue("font_on_map", defaut=as_default))
        self.btn_color_chaine.setColor(QColor(self.params.getValue("color_font_on_map", defaut=as_default)))
        self.btn_color_dist.setColor(QColor(self.params.getValue("mesure_line_color", defaut=as_default)))
        self.chk_keep_marker.setChecked(self.params.getValue("keep_marker_suivi_chainage", defaut=as_default))
        self.chx_marqueur_exact.setChecked(self.params.getValue("pos_marqueur_arrondi", defaut=as_default))
        self.spx_dist_interpolation.setValue(self.params.getValue("dist_interpolation", defaut=as_default))
        self.spx_intervalle_interpolation.setValue(self.params.getValue("intervalle_interpolation", defaut=as_default))
        self.gbx_create_layer_chainage.setChecked(self.params.getValue("use_layer_recherche_chainage", defaut=as_default))
        self.layer_chainage_name.setText(self.params.getValue("layer_recherche_chainage_name", defaut=as_default))
        self.rbt_planiactif.setChecked(self.params.getValue("open_sigo_plainiactif", defaut=as_default))

        # Définir les raccourcis clavier à partir du dictionnaire
        for param_name, widjet in self.raccourci.items():
            shortcut = self.params.getValue(param_name, defaut=as_default)
            widjet["chx"].setChecked(shortcut != "")
            widjet["key"].setKeySequence(QKeySequence(shortcut))

        # Définir les case à cocher du groupe pour afficher un tooltip
        group_box_check = False
        for param_name, widget in self.checkbox_tooltip.items():
            state = self.params.getValue(param_name, defaut=as_default)
            widget.setChecked(state)
            if state: group_box_check = True
        self.gbx_show_tooltip.setChecked(group_box_check)
        
        # Parcourir les widget de case a cocher et définir son état et l'icon de l'action associé
        for action_name, widget in self.widgets_action.items():
            # Action associé au widjet
            action = self.params.getAction(action_name)
            # Définir son état (coché/décoché)
            if action: widget.setChecked(action.get(defaut=as_default))
    
    def initialiseAllDefaultValues(self):
        """ Permet de réinitialiser toutes les valeurs avec leur valeurs par défault """
        # Assurer que l'utilisateur veux bien faire le reset
        reply = QMessageBox.question(
            self.iface.mainWindow(),
            'Attention!',
            f'Voulez-vous vraiment réinitialiser toutes les valeurs par default?<br><br><i>À noter qu\'ils ne seront pas enregistrer tant que le bouton "Enregistrer" sera cliqué.</i>',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        # Reset les paramètre par défaut selon la confirmation de l'utilisateur 
        if reply == QMessageBox.Yes: self.initialisePresentValues(as_default=True)
        else: self.raise_()

    def saveSettings(self):
        self.params.setValue("layer_rtss", self.txt_layer_rtss.text())
        self.params.setValue("field_num_rtss", self.txt_field_rtss.text())
        self.params.setValue("field_chainage_fin", self.txt_field_chainage_fin.text())
        self.params.setValue("field_chainage_debut", self.txt_field_chainage_debut.text())
        self.params.setValue("field_classification", self.txt_field_class.text())
        
        self.params.setValue("load_custom_expressions", self.chx_add_expressions.isChecked())
        self.params.setValue("formater_rtss", self.chx_format_rtss.isChecked())
        self.params.setValue("formater_chainage", self.chx_format_chainage.isChecked())
        self.params.setValue("show_copie_menu_formater", self.chk_copie_formater.isChecked())
        self.params.setValue("show_copie_menu_info", self.chk_copie_info_rtss.isChecked())
        self.params.setValue("show_marker_direction", self.chx_marqueur_dir.isChecked())
        self.params.setValue("show_copie_menu_non_formater", self.chk_copie_non_formater.isChecked())
        self.params.setValue("use_only_on_visible", self.chx_use_visible.isChecked())
        self.params.setValue("keep_marker_suivi_chainage", self.chk_keep_marker.isChecked())
        self.params.setValue("precision_chainage", self.spx_precision.value())
        self.params.setValue("precision_mesure", self.spx_precision_mesure.value())
        self.params.setValue("precision_distance", self.spx_precision_dist.value())
        self.params.setValue("layer_ecusson_name", self.txt_layer_ecusson.text())
        self.params.setValue("layer_ecusson_field_route", self.txt_champ_route.text())
        self.params.setValue("layer_ecusson_field_classe", self.txt_champ_classe.text())
        self.params.setValue("layer_ecusson_style", self.txt_sybologie_ecusson.text())
        self.params.setValue("layer_chainage_style", self.txt_sybologie_chainage.text())
        self.params.setValue("layer_transect_style", self.txt_sybologie_transect.text())
        self.params.setValue("layer_atlas_style", self.txt_sybologie_atlas.text())
        self.params.setValue("pos_marqueur_arrondi", self.chx_marqueur_exact.isChecked())
        self.params.setValue("use_layer_recherche_chainage", self.gbx_create_layer_chainage.isChecked())
        self.params.setValue("layer_recherche_chainage_name", self.layer_chainage_name.text())
        self.params.setValue("open_sigo_plainiactif", self.rbt_planiactif.isChecked())

        # Save the settings for the context layer tab
        self.saveContextLayerSettings()
        
        # Set raccourci pour le suivi du chainage
        set_raccourci = self.chk_shorcut_chainage.isChecked()
        self.params.setValue("use_raccourcis_chainage", set_raccourci)
        if set_raccourci: self.params.setValue("raccourcis_clavier", self.key_shortcut.keySequence().toString())
        # Set raccourci pour le placement d'éccussons
        set_raccourci = self.chk_shorcut_ecusson.isChecked()
        self.params.setValue("use_raccourcis_ecusson", set_raccourci)
        if set_raccourci: self.params.setValue("raccourcis_clavier_ecusson", self.key_shortcut_ecusson.keySequence().toString())
        # Set raccourci pour la mesure de distance
        set_raccourci = self.chk_shorcut_distance.isChecked()
        self.params.setValue("use_raccourcis_distance", set_raccourci)
        if set_raccourci: self.params.setValue("raccourcis_clavier_distance", self.key_shortcut_distance.keySequence().toString())
        
        # Définir les raccourcis clavier à partir du dictionnaire
        for param_name, widjet in self.raccourci.items():
            if widjet["chx"].isChecked(): self.params.setValue(param_name, widjet["key"].keySequence().toString())
            else:  self.params.setValue(param_name, "")

        self.params.setValue("font_on_map", self.mFontButton.currentFont())
        self.params.setValue("color_font_on_map", self.btn_color_chaine.color().name())
        self.params.setValue("mesure_line_color", self.btn_color_dist.color().name())
        
        group_box_check = self.gbx_show_tooltip.isChecked()
        for param_name, widget in self.checkbox_tooltip.items():
            if group_box_check: self.params.setValue(param_name, widget.isChecked())
            else: self.params.setValue(param_name, False)
        
        for action_name, widget in self.widgets_action.items():
            action = self.params.getAction(action_name)
            if action.get() != widget.isChecked(): action.set(widget.isChecked())
        
        self.parametre_updated.emit()
        
        self.close()
        Utilitaire.succesMessage(self.iface, " Les paramètres enregistrés avec succès!", subject="Plugin chainage MTQ:")    

    def saveContextLayerSettings(self):
        """ Permet d'enregistrer les paramètres pour la Tab de la couche de context """
        self.params.setValue("context_layer", self.cbx_layer_context.currentText())
        self.params.setValue("field_context_value", self.cbx_field_value.currentField())
        self.params.setValue("field_context_route", self.cbx_field_route.currentField())
        self.params.setValue("dist_interpolation", self.spx_dist_interpolation.value())
        self.params.setValue("intervalle_interpolation", self.spx_intervalle_interpolation.value())

    def selectionnerCoucheRTSS(self):
        # Assurer qu'il y ai au moins 1 couches dans le LayerManager
        if QgsProject.instance().count() == 0:
            return QMessageBox.warning(self, "Attention", "Aucune couche n'est présente dans le projet!")
        
        dlg_couche = fenetreSelectionCouche(
            layer_rtss_name=self.txt_layer_rtss.text(),
            field_rtss_name=self.txt_field_rtss.text(),
            field_chainage_f_name=self.txt_field_chainage_fin.text(),
            field_chainage_d_name=self.txt_field_chainage_debut.text(),
            field_class_name=self.txt_field_class.text(),
            parent=self)

        # Ouvrir la fenêtre et attendre une selection
        if dlg_couche.exec_() == QDialog.Accepted:
            self.txt_layer_rtss.setText(dlg_couche.cbx_layer_rtss.currentText())
            self.txt_field_rtss.setText(dlg_couche.cbx_field_rtss.currentField())
            self.txt_field_chainage_fin.setText(dlg_couche.cbx_field_chainage.currentField())
            self.txt_field_chainage_debut.setText(dlg_couche.cbx_field_chainage_d.currentField())
            self.txt_field_class.setText(dlg_couche.cbx_field_class.currentField())

    def choisirQML(self, line_edit):
        line_edit.setText(choisirFichier("Ouvrir un fichier de style", "QGIS Layer Settings (*.qml)", line_edit.text()))
        
    def checkKeyShortcutChainage(self, key_sequence):
        validation_text = ""
        if key_sequence.toString() != self.params.getValue("raccourcis_clavier"):
            if checkIfKeySequenceExists(key_sequence):
                validation_text = f"Attention! Le raccourci {key_sequence.toString()} est déjà associé à une action"
        self.lbl_key_chainage.setText(validation_text)
    
    def checkKeyShortcutEcusson(self, key_sequence):
        validation_text = ""
        if key_sequence.toString() != self.params.getValue("raccourcis_clavier_ecusson"):
            if checkIfKeySequenceExists(key_sequence):
                validation_text = f"Attention! Le raccourci {key_sequence.toString()} est déjà associé à une action"
        self.lbl_key_ecusson.setText(validation_text)

    def checkKeyShortcutDistance(self, key_sequence):
        validation_text = ""
        if key_sequence.toString() != self.params.getValue("raccourcis_clavier_distance"):
            if checkIfKeySequenceExists(key_sequence):
                validation_text = f"Attention! Le raccourci {key_sequence.toString()} est déjà associé à une action"
        self.lbl_key_distance.setText(validation_text)
        
    def generateContextLayerIndex(self):
        """ Permet d'enregistrer les paramètres et d'emmetre le signal pour générer le réseau """
        self.saveContextLayerSettings()
        self.generate_index.emit()