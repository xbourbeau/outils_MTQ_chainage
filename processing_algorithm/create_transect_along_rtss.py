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
                       QgsProcessingParameterBoolean,
                       QgsField,
                       QgsFields,
                       QgsFeature,
                       QgsWkbTypes)
import numpy as np

from ..mtq.core import Geocodage, Chainage

class generateTransect(QgsProcessingAlgorithm):
    """ Permet de générer des lignes perpendiculaire à un certain interval le long d'une ligne. """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_RTSS = 'INPUT_RTSS'
    RTSS = 'RTSS'
    LONG = 'LONG'
    INPUT_INTERVAL = 'INPUT_INTERVAL'
    INPUT_LINE_LENGTH_DROITE = 'INPUT_LINE_LENGTH_DROITE'
    INPUT_LINE_LENGTH_GAUCHE = 'INPUT_LINE_LENGTH_GAUCHE'
    OUTPUT = 'OUTPUT'
    INVERSE = 'INVERSE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return generateTransect()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'generateTransect'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Transects le long de RTSS")

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
        return "file://sstao00-adm005/TridentAnalyst/Plugin_chainage_mtq/Documentation/Index.html#subsection4-5"
    
    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("L'Agorithme permet de créer des lignes perpendiculaire à un interval de chainage le long d\'un RTSS")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # =================== Paramètres ===================
        
        # ------------------- INPUT_RTSS -------------------
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_RTSS,
                self.tr('Couche des RTSS'),
                [QgsProcessing.TypeVectorLine]))
        
        # ------------------- Champ RTSS -------------------
        parametre_rtss = QgsProcessingParameterField(
                self.RTSS,
                self.tr('Numéro de RTSS'),
                'num_rts',
                self.tr(self.INPUT_RTSS))
        #parametre_rtss.setDataType(1)
        self.addParameter(parametre_rtss)
        
        # ------------------- Champ LONG -------------------
        parametre_chainage_f = QgsProcessingParameterField(
                self.LONG,
                self.tr('Chainage de fin du RTSS'),
                'val_longr_sous_route',
                self.tr(self.INPUT_RTSS))
        #parametre_chainage_f.setDataType(0)
        self.addParameter(parametre_chainage_f)
        
        # ------------------- INPUT_INTERVAL -------------------
        parametre_dist = QgsProcessingParameterDistance (
                            self.INPUT_INTERVAL,
                            self.tr('Interval de chainage'),
                            defaultValue=20,
                            minValue=0.01)
        parametre_dist.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        self.addParameter(parametre_dist)
        
        # ------------------- INPUT_LINE_LENGTH_DROITE -------------------
        parametre_long_droite = QgsProcessingParameterDistance (
                            self.INPUT_LINE_LENGTH_DROITE,
                            self.tr('Longueur de lignes à droite de la chaussée'),
                            defaultValue=20,
                            minValue=0.01
                        )
        parametre_long_droite.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        self.addParameter(parametre_long_droite)
        
        # ------------------- INPUT_LINE_LENGTH_GAUCHE -------------------
        parametre_long_gauche = QgsProcessingParameterDistance (
                            self.INPUT_LINE_LENGTH_GAUCHE,
                            self.tr('Longueur de lignes à gauche de la chaussée'),
                            defaultValue=20,
                            minValue=0.01
                        )
        parametre_long_gauche.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        self.addParameter(parametre_long_gauche)
        
        # ------------------- INVERSE -------------------
        self.addParameter(QgsProcessingParameterBoolean(
                            self.INVERSE,
                            self.tr('True: droite à gauche False: gauche à droite'),
                            False))

        
        # ------------------- OUTPUT -------------------
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Transects')))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source_rtss = self.parameterAsSource(parameters, self.INPUT_RTSS, context)
        
        # If source was not found, throw an exception
        if not source_rtss:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_RTSS))
        
        champ_rtss = self.parameterAsString(parameters, self.RTSS, context)
        champ_long = self.parameterAsString(parameters, self.LONG, context)
        
        # Verifier que le paramêtre n'est pas vide
        if not champ_rtss:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.RTSS))
        if not champ_long:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LONG))
        
        
        # Aller chercher la valeur de l'interval de distance
        interval_dist = self.parameterAsDouble(parameters, self.INPUT_INTERVAL, context)
        # Verifier que le paramêtre n'est pas vide
        if not interval_dist:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_INTERVAL))
            
        # Aller chercher la valeur de la longueur des lignes
        dist_droite = self.parameterAsDouble(parameters, self.INPUT_LINE_LENGTH_DROITE, context)
        # Verifier que le paramêtre n'est pas vide
        if not dist_droite:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LINE_LENGTH_DROITE)) 

         # Aller chercher la valeur de la longueur des lignes
        dist_gauche = self.parameterAsDouble(parameters, self.INPUT_LINE_LENGTH_GAUCHE, context)
        # Verifier que le paramêtre n'est pas vide
        if not dist_gauche:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LINE_LENGTH_GAUCHE))
        
        # Aller chercher la valeur de la longueur des lignes
        inverse = self.parameterAsBool(parameters, self.INVERSE, context)
        
        
        fields = QgsFields()
        for field in [QgsField("RTSS", QVariant.String),
                        QgsField("chainage", QVariant.Double),
                        QgsField("chainage_format", QVariant.String),
                        QgsField("long", QVariant.Int),
                        QgsField("dist_d", QVariant.Double),
                        QgsField("dist_g", QVariant.Double)]:
            fields.append(field)
                        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            source_rtss.sourceCrs()
        )

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source_rtss.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source_rtss.featureCount() if source_rtss.featureCount() else 0
        
        geocode = Geocodage(source_rtss.getFeatures(), source_rtss.sourceCrs(),
                            champ_rtss, champ_long, precision=5)
        
        for current, feat_rtss in enumerate(geocode.getListFeatRTSS()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled(): break
            chainage_f = int(feat_rtss.chainageFin())
            # Nombre de point à créer sur le RTSS
            longeur_ajuster = chainage_f-(chainage_f%interval_dist)
            
            # Parcourire chaque interval du RTSS
            for chainage in np.arange(0, longeur_ajuster+interval_dist, interval_dist):
                feedback.pushInfo('long_ajust {}'.format(chainage))
                perpendicular_line = feat_rtss.getTransect(chainage, dist_droite, dist_gauche, inverse)
                longueur_ligne = dist_droite + dist_gauche
                feat = QgsFeature()
                feat.setGeometry(perpendicular_line)
                feat.setAttributes([feat_rtss.value(), float(chainage), Chainage(chainage).valueFormater(), longueur_ligne, dist_droite, dist_gauche])
                # Add a feature in the sink
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
                
            if chainage_f != longeur_ajuster:
                perpendicular_line = feat_rtss.getTransect(chainage_f, dist_droite, dist_gauche, inverse)
                longueur_ligne = dist_droite + dist_gauche
                feat = QgsFeature()
                feat.setGeometry(perpendicular_line)
                feat.setAttributes([feat_rtss.value(), chainage_f, Chainage(chainage_f).valueFormater(), longueur_ligne, dist_droite, dist_gauche])
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
