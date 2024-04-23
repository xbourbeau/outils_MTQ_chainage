# -*- coding: utf-8 -*-
from qgis.core import (Qgis, QgsVectorLayer, QgsTask, QgsMessageLog)
from .LayerMTQ import LayerMTQ

class LoadLayers(QgsTask):
    """ Subclass of QgsTask pour charger la source de plusieur couches """
    def __init__(self, layers:dict[str, LayerMTQ], **kwargs):
        super().__init__('Load layers', QgsTask.CanCancel)
        self.layers = layers
        self.result_layers = {}
        self.datasources = {}
        for layer_name, layer in self.layers.items():
            self.datasources[layer_name] = layer.dataSource(**kwargs)
        self.exception = None

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), "Load layers", Qgis.Info)
        try:
            QgsMessageLog.logMessage(f"Loading layers: {', '.join(list(self.layers.keys()))} loaded!", "Load layers", Qgis.Info)
            total = len(self.layers)
            for i, (layer_name, layer) in enumerate(self.layers.items()):
                self.result_layers[layer_name] = QgsVectorLayer(self.datasources[layer_name], layer_name, layer.dataProvider())
                self.setProgress((i+1*100)/total)
                QgsMessageLog.logMessage(f"Layer {layer_name} loaded!", "Load layers", Qgis.Info)
                if self.isCanceled(): return False
        # Throw exception
        except Exception as e:
            self.exception = e
            return False
        return True

    def finished(self, result):
        if result: QgsMessageLog.logMessage('"{name}" completed\n'.format(name=self.description()), "Load layers", Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage('"{name}" not successful but without exception (probably the task was manually canceled by the user)'.format(name=self.description()), "Load layers", Qgis.Warning)
            else:
                QgsMessageLog.logMessage('"{name}" Exception: {exception}'.format(name=self.description(),exception=self.exception), "Load layers", Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage('"{name}" was canceled'.format(name=self.description()),"Load layers", Qgis.Info)
        super().cancel()
        
    def getLayers(self)->dict[str, LayerMTQ]: 
        return self.result_layers
