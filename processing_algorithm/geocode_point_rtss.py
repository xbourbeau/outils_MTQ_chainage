# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsPropertyDefinition,
                       QgsWkbTypes,
                       QgsGeometry,
                       QgsField,
                       QgsFeature,
                       QgsRaster,
                       QgsPointXY,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink)

from ..mtq.core import Geocodage, Chainage

class GeocodePoint(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_RTSS = 'INPUT_RTSS'
    RTSS = 'RTSS'
    LONG = 'LONG'
    GEOCODE = 'GEOCODE'
    RTSSFIELD = 'RTSSFIELD'
    CHAINE = 'CHAINE'
    DISTTRACE = 'DISTTRACE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GeocodePoint()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Geocodep'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Géocoder (point)')

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
        return "file://sstao00-adm005/TridentAnalyst/Plugin_chainage_mtq/Documentation/Index.html#subsection4-2"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("""
            Géocoder des points à partir d'un RTSS et d'un chainage. Un offset peut aussi être spécifié.
            Un offset positive représente un décalage à droite alors qu'un offset négative représente un décalage à gauche.
                        """)

    def initAlgorithm(self, config=None):
        """
        Here we define the INPUT_RTSSs and output of the algorithm, along
        with some other properties.
        """
        # =================== Paramètres ===================
        # We add the INPUT_RTSS vector features source. It can have any kind of
        # geometry.
        # ------------------- INPUT_RTSS -------------------
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_RTSS,
                self.tr('Couche des RTSS'),
                [QgsProcessing.TypeVectorLine],
                'BGR - RTSS'))
        
        # ------------------- Champ RTSS -------------------
        self.addParameter(
            QgsProcessingParameterField(
                self.RTSS,
                self.tr('Numéro de RTSS'),
                'num_rts',
                self.tr(self.INPUT_RTSS)))
                
        # ------------------- Champ LONG -------------------
        self.addParameter(
            QgsProcessingParameterField(
                self.LONG,
                self.tr('Chainage de fin des RTSS'),
                'val_longr_sous_route',
                self.tr(self.INPUT_RTSS)))
                
        # ------------------- Fichier à géocoder -------------------
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.GEOCODE,
                self.tr('Fichier à géocoder'),
                [QgsProcessing.TypeFile]))
                
        # ------------------- colone rtss -------------------
        self.addParameter(
            QgsProcessingParameterField(
                self.RTSSFIELD,
                self.tr('Numéro de RTSS'),
                'RTSS',
                self.tr(self.GEOCODE),
                type=QgsProcessingParameterField.String))
                
        # ------------------- colone chainage -------------------
        self.addParameter(
            QgsProcessingParameterField(
                self.CHAINE,
                self.tr('Chainage'),
                'chainage',
                self.tr(self.GEOCODE),
                type=QgsProcessingParameterField.Numeric|QgsProcessingParameterField.String))
                
        # ------------------- offset -------------------
        self.addParameter(QgsProcessingParameterField(
                self.DISTTRACE,
                self.tr('Distance de décalage'),
                None,
                self.tr(self.GEOCODE),
                type=QgsProcessingParameterField.Numeric,
                optional=True))
        
        # ------------------- OUTPUT -------------------
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source_rtss = self.parameterAsVectorLayer(parameters, self.INPUT_RTSS, context)
        if not source_rtss:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_RTSS))
        
        champ_rtss_1 = self.parameterAsString(parameters, self.RTSS, context)
        
        champ_chainage_1 = self.parameterAsString(parameters, self.LONG, context)
        
        file_geocoder = self.parameterAsLayer(parameters, self.GEOCODE, context)
        # Verifier que le paramètre n'est pas vide
        if not file_geocoder:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.GEOCODE))
        
        champ_rtss_2 = self.parameterAsString(parameters, self.RTSSFIELD, context)
        
        champ_chainage_2 = self.parameterAsString(parameters, self.CHAINE, context)
        
        champ_offset = self.parameterAsString(parameters, self.DISTTRACE, context)
        
        fields = file_geocoder.fields()
        fields.append(QgsField("valide", QVariant.Bool))
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            source_rtss.sourceCrs())
        if not sink:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source_rtss.sourceCrs().authid()))
        
        geocode = geocodage(source_rtss.getFeatures(), source_rtss.sourceCrs(),
                            champ_rtss_1, champ_chainage_1)
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / file_geocoder.featureCount() if file_geocoder.featureCount() else 0
        feat_total = 0
        
        for current, feature in enumerate(file_geocoder.getFeatures()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled(): break
            if champ_offset: offset = feature[champ_offset]
            else: offset = 0
            
            geom = geocode.geocoder(feature[champ_rtss_2], verifyFormatChainage(feature[champ_chainage_2]), offset=offset)
            is_valide = True
            if not geom:
                # Send some information to the user
                feedback.pushWarning('L\'entité {} n\'a pas été géocodée: Le rtss {} n\'est pas dans la couche des rtss'.format(feature.id(), feature[champ_rtss_2]))
                is_valide = False
            else: feat_total += 1
                
            feat = QgsFeature()
            feat.setGeometry(geom)
            attrs = feature.attributes()
            attrs.append(is_valide)
            feat.setAttributes(attrs)
            # Add a feature in the sink
            sink.addFeature(feat, QgsFeatureSink.FastInsert)
            
            # Update the progress bar
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo('{} entitée géocodées'.format(feat_total))
        
        return {self.OUTPUT: dest_id}
