# -*- coding: utf-8 -*-
from qgis.core import QgsTask, QgsMessageLog, Qgis
from ..mtq.core import ReseauSegmenter

MESSAGE_CATEGORY = 'Index reseau segementé'

class TaskGenerateReseauSegementation(QgsTask):

    def __init__(self, geocode, layer_context, field_value, field_rtss, interval, dist_max):
        self.geocode = geocode
        self.layer_context = layer_context
        self.field_value = field_value
        self.field_rtss = field_rtss
        self.interval = interval
        self.dist_max = dist_max
        # Suivi des erreurs
        self.exception = None
        self.reseau_context = None
        super().__init__(MESSAGE_CATEGORY, QgsTask.CanCancel)

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage("Information:", MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(f"   - Nombre de RTSS: {len(self.geocode)}", MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(f"   - La couche utilisé: {self.layer_context.name()}", MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(f"   - Le champs de la valeur: {self.field_value}", MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(f"   - Le champs du numéro de route: {self.field_rtss}", MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(f"   - La distance maximal de la trace du RTSS: {self.dist_max}m", MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(f"   - La distance des intervalles de points interpolés: {self.interval}m", MESSAGE_CATEGORY, Qgis.Info)
        
        self.setProgress(0)
        QgsMessageLog.logMessage('Création du réseau...', MESSAGE_CATEGORY, Qgis.Info)
        try:
            # Créer le réseau
            self.reseau_context = ReseauSegmenter.fromInterpolation(
                geocode=self.geocode,
                layer=self.layer_context,
                field_value=self.field_value,
                fields_route=self.field_rtss,
                step=self.interval,
                max_dist=self.dist_max)
        except Exception as error:
            self.exception = error
            return False
        return True

    def finished(self, result):
        if result: QgsMessageLog.logMessage('"{name}" completed\n'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage( '"{name}" not successful but without exception (probably the task was manually canceled by the user)'.format(name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage( '"{name}" Exception: {exception}'.format(name=self.description(), exception=self.exception), MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage('"{name}" was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

    def getReseau(self): return self.reseau_context


        
        
        
        
        
        
        
        
        
        
        
        
        