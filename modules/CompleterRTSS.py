
from qgis.PyQt.QtCore import QStringListModel
from qgis.PyQt.QtWidgets import QCompleter

from ..mtq.core import Geocodage

class CompleterRTSS(QCompleter):
    
    """ Custom QComplter pour identifier des RTSS """

    def __init__(self, geocode:Geocodage, parent=None, formater_rtss=True):
        super().__init__(parent)
        # Définir le searche engine use to complete text
        self.geocode = geocode
        # Indicateur que les RTSS devraient être formaté
        self.formater_rtss = formater_rtss
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setCaseSensitivity(False)
        self.setMaxVisibleItems(5)

        self.model = QStringListModel()
        self.setModel(self.model)

    def splitPath(self, text):
        """ Overridden method to return completions based on reversed input. """
        filtered_choices = []
        # Parcourir les RTSS possible 
        for rtss in self.geocode.search(text, limit=5, as_rtss=True):
            # Ajouter les RTSS à la liste
            filtered_choices.append(rtss.value(formater=self.formater_rtss))
        # Définir les valeurs possible au QCompleter
        self.model.setStringList(filtered_choices)
        # Retrourner rien pour qu'il match avec toutes les valeurs défini
        return [""]