# -*- coding: utf-8 -*-
from qgis.core import (Qgis, QgsVectorLayer, QgsTask, QgsMessageLog)

class LoadLayer(QgsTask):
    """ Subclass of QgsTask pour charger la source de plusieur couches """
    def __init__(self, data_source, layer_name, provider):
        super().__init__('Load layer', QgsTask.CanCancel)
        self.data_source = data_source
        self.layer_name = layer_name
        self.provider = provider
        self.layer = None
        self.exception = None

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), "Load layers", Qgis.Info)
        try:
            if self.isCanceled(): return False
            QgsMessageLog.logMessage(f"Loading layer {self.layer_name}", "Load layers", Qgis.Info)
            self.layer = QgsVectorLayer(self.data_source, self.layer_name, self.provider)
            QgsMessageLog.logMessage(f"Layer {self.layer_name} loaded!", "Load layers", Qgis.Info)
            if self.isCanceled(): return False
        # Throw exception
        except Exception as e:
            self.exception = e
            return False
        return True

    def finished(self, result):
        if result: QgsMessageLog.logMessage('"{name}" completed\n'.format(name=self.description()), "Load layer", Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage('"{name}" not successful but without exception (probably the task was manually canceled by the user)'.format(name=self.description()), "Load layers", Qgis.Warning)
            else:
                QgsMessageLog.logMessage('"{name}" Exception: {exception}'.format(name=self.description(),exception=self.exception), "Load layer", Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage('"{name}" was canceled'.format(name=self.description()),"Load layer", Qgis.Info)
        super().cancel()
        
    def getLayer(self): return self.layer
