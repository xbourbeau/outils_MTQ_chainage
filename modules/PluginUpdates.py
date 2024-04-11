# -*- coding: utf-8 -*-
from packaging import version
import os.path
import pyplugin_installer
from qgis.PyQt.QtWidgets import QPushButton
# Class pour la gestion des paramètre du plugin
from ..gestion_parametres import sourceParametre


class PluginUpdates:

    def __init__(self, iface, current_version):
        self.iface = iface
        # La version du plugin actif
        self.current_version = current_version
        # Le chemin vers le fichier zip de l'installation du nouveau plugin disponible
        self.new_plugin = None
        # La nouvelle version du plugin disponible
        self.new_version = None
        # Class qui gère l'enregistrement des paramètres
        self.gestion_parametre = sourceParametre()
    
    """ Méthode qui vérifie si une nouvelle version du plugin est disponnible """
    def checkForPluginUpdate(self):
        try:
            if self.gestion_parametre.getParam("suivi_plugin_update").getValue():
                plugins_path = self.gestion_parametre.getParam("dossier_plugin_update").getValue()
                # Vérifier que le chemin est valide
                if os.path.exists(plugins_path):
                    # Inisialiser la nouvelle version avec la version courant
                    new_version = self.current_version
                    # Parcourir les fichiers du répertoire des plugins
                    for plugin_file in os.listdir(plugins_path):
                        try:
                            # Vérifier si le ficher est un fichier compressé 
                            if plugin_file[-4:] == '.zip' :
                                # Garder seulement la portion du numéro de version
                                plugin_file_version = plugin_file[:-4].split('_v')[1]
                                # Comparer la version du fichier ZIP dans le répertoire avec la nouvelle version courante
                                if version.parse(new_version) < version.parse(plugin_file_version): 
                                    # La version du ZIP est plus récente que la version courante
                                    new_version = plugin_file_version
                                    # Garder le chemin vers le ZIP
                                    new_plugin = os.path.join(plugins_path, plugin_file)
                        except: continue
                    # Vérifier si une nouvelle version à été trouvé
                    if new_version != self.current_version:
                        self.new_plugin = new_plugin
                        # Vérifier si une nouvelle version à été trouvé
                        text = ('<b>Une nouvelle version du plugin de chainage est disponible!</b>'
                                ' La version %s est disponible pour installation') % (new_version)
                        popWidget = self.iface.messageBar().createMessage(text)
                        button = QPushButton(popWidget)
                        button.setText("Installer")
                        button.pressed.connect(self.installNewVersion)
                        popWidget.layout().addWidget(button)
                        a = self.iface.messageBar().pushWidget(popWidget, 0)
        except: pass
        
    
    """ Méthode qui permet d'installer la nouvelle version du plugin """
    def installNewVersion(self):
        self.iface.messageBar().popWidget(self.iface.messageBar().currentItem())
        pyplugin_installer.instance().installFromZipFile(self.new_plugin)
    
    
    
    
pass