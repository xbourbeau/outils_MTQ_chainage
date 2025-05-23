# -*- coding: utf-8 -*-
from PyQt5.QtCore import (  QCoreApplication,
                            QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterDistance,
                       QgsUnitTypes,
                       QgsProcessingParameterFeatureSink,
                       QgsField,
                       QgsFields,
                       QgsFeature,
                       QgsWkbTypes)

from ..mtq.core import Geocodage, Chainage
import numpy as np


class generateChainagePointOnRTSS(QgsProcessingAlgorithm):
    """
    Fonction qui permet de générer des points le long d'un RTSS en fonction
    d'un interval de chaînage
    """
    
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    INPUT_RTSS = 'INPUT_RTSS'
    INPUT_FIELD_RTSS = 'INPUT_FIELD_RTSS'
    INPUT_FIELD_LONG = 'INPUT_FIELD_LONG'
    INPUT_INTERVAL = 'INPUT_INTERVAL'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return generateChainagePointOnRTSS()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'generateChainagePointOnRTSS'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Points de chainage sur un RTSS')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('RTSS')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'rtss'

    def helpUrl(self):
        return "file://sstao00-adm005/TridentAnalyst/Plugin_chainage_mtq/Documentation/Index.html#subsection4-4"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("L'Agorithme permet de créer une couche de points représentant les chainages d'un RTSS selon l'interval défini.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # =================== Paramètres ===================
        
        # ------------------- INPUT_RTSS -------------------
        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_RTSS,
                self.tr('Couche des RTSS'),
                [QgsProcessing.TypeVectorLine],
                'BGR - RTSS'))
        
        # ------------------- Champ RTSS -------------------
        self.addParameter(
            QgsProcessingParameterField(
                name=self.INPUT_FIELD_RTSS,
                description=self.tr('Numéro de RTSS'),
                defaultValue='num_rts',
                parentLayerParameterName=self.INPUT_RTSS,
                type=QgsProcessingParameterField.String))
        
        # ------------------- Champ chainage fin -------------------
        self.addParameter(
            QgsProcessingParameterField(
                name=self.INPUT_FIELD_LONG,
                description=self.tr('Chainage de fin du RTSS'),
                defaultValue='val_longr_sous_route',
                parentLayerParameterName=self.INPUT_RTSS,
                type=QgsProcessingParameterField.Numeric))
        
        # ------------------- Intervalle -------------------
        parametre_dist = QgsProcessingParameterDistance (
                            self.INPUT_INTERVAL,
                            self.tr('Interval de chainage'),
                            defaultValue=10,
                            minValue=0.000001)
        parametre_dist.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        self.addParameter(parametre_dist)
        
        # ------------------- Output -------------------
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Intervalles de chainage')))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source_rtss = self.parameterAsSource(parameters, self.INPUT_RTSS, context)
        # If source was not found, throw an exception
        if source_rtss is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_RTSS))
        
        # Aller chercher la valeur du champs RTSS
        champ_rtss = self.parameterAsString(parameters, self.INPUT_FIELD_RTSS, context)
        
        # Aller chercher la valeur du champs chainage de fin 
        champ_chainage_f = self.parameterAsString(parameters, self.INPUT_FIELD_LONG, context)
        
        # Aller chercher la valeur de l'interval de distance
        interval_dist = self.parameterAsDouble(parameters, self.INPUT_INTERVAL, context)
        
        # Définir le type de champs de chainage selon la distance
        if int(interval_dist) == interval_dist: type = QVariant.Int
        else: type = QVariant.Double
        fields = QgsFields()
        for field in [QgsField("RTSS", QVariant.String),
                        QgsField("Chainage", QVariant.Double),
                        QgsField("Chainage_formater", QVariant.String),
                        QgsField("Angle", QVariant.Double)]:
            fields.append(field)
                        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            source_rtss.sourceCrs())

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source_rtss.sourceCrs().authid()))

        # If sink was not created, throw an exception
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source_rtss.featureCount() if source_rtss.featureCount() else 0
        
        geocode = Geocodage(source_rtss.getFeatures(), source_rtss.sourceCrs(),
                            champ_rtss, champ_chainage_f)
        
        for current, feat_rtss in enumerate(geocode.getListFeatRTSS()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled(): break
            chainage_f = int(feat_rtss.chainageFin())
            # Nombre de point à créer sur le RTSS
            longeur_ajuster = int(chainage_f-(chainage_f%interval_dist))
            
            # Parcourire chaque interval du RTSS
            for chainage in np.arange(0, longeur_ajuster+interval_dist, interval_dist):
                point_chainage = feat_rtss.geocoderPointFromChainage(chainage)
                angle = feat_rtss.getAngleAtChainage(chainage)
                feat = QgsFeature()
                feat.setGeometry(point_chainage)
                feat.setAttributes([feat_rtss.value(), float(chainage), Chainage(chainage).valueFormater(), angle])
                # Add a feature in the sink
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
                
            if chainage_f != longeur_ajuster:
                point_chainage = feat_rtss.geocoderPointFromChainage(chainage_f)
                angle = feat_rtss.getAngleAtChainage(chainage_f)
                feat = QgsFeature()
                feat.setGeometry(point_chainage)
                feat.setAttributes([feat_rtss.value(), float(chainage_f), Chainage(chainage_f).valueFormater(), angle])
                # Add a feature in the sink
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
            
            # Update the progress bar
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}
        