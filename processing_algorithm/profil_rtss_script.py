# -*- coding: utf-8 -*-
from PyQt5.QtCore import (  QCoreApplication,
                            QVariant)
from qgis.core import (QgsProcessing,
                        QgsProject, QgsCoordinateTransform,
                        QgsFeatureSink, QgsRaster, QgsProcessingParameterField,
                        QgsProcessingException,
                        QgsProcessingAlgorithm,
                        QgsProcessingParameterFeatureSource,
                        QgsProcessingParameterRasterLayer,
                        QgsProcessingParameterDistance,
                        QgsUnitTypes, QgsCoordinateReferenceSystem,
                        QgsProcessingParameterFeatureSink,
                        QgsField, QgsFields, QgsFeature, QgsWkbTypes,
                        QgsGeometry, QgsPoint, QgsPointXY, 
                        NULL)
'''
Fonction qui permet de générer des points le long d'un RTSS en fonction
d'un interval de chaînage
'''
class generateRTSSProfilFromMNT(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_RTSS = 'INPUT_RTSS'
    INPUT_INTERVAL = 'INPUT_INTERVAL'
    INPUT_FIELD_RTSS = 'INPUT_FIELD_RTSS'
    INPUT_MNT = 'INPUT_MNT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return generateRTSSProfilFromMNT()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'generater3dline'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Générer trace 3D')

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
        return "file://sstao00-adm005/TridentAnalyst/Plugin_chainage_mtq/Documentation/Index.html#subsection4-1"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("L'Agorithme permet de créer une trace 3D de la route à partir d'un MNT")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_RTSS,
                self.tr('Entrée de la couche des RTSS'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD_RTSS,
                self.tr('Champ du numéro de RTSS'),
                'num_rts',
                self.INPUT_RTSS,
                type=1,
                optional=True
            )
        )
        
        parametre_dist = QgsProcessingParameterDistance (
                            self.INPUT_INTERVAL,
                            self.tr('Interval des points de chainage à générer'),
                            0,
                            minValue=0)
                            
        parametre_dist.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        parametre_dist.setDataType(0) # Nombre entier
        self.addParameter(parametre_dist)
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_MNT,
                self.tr('MNT en entrée'))
        )
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Trace 3D')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source_RTSS = self.parameterAsSource(
            parameters,
            self.INPUT_RTSS,
            context
        )
        # If source was not found, throw an exception
        if source_RTSS is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_RTSS))

        # Aller chercher la valeur du champs RTSS
        field_rtss = self.parameterAsString(
            parameters,
            self.INPUT_FIELD_RTSS,
            context
        )

        # Aller chercher la valeur de l'interval de distance
        interval_dist = self.parameterAsInt(
            parameters,
            self.INPUT_INTERVAL,
            context
        )
        
        source_MNT = self.parameterAsRasterLayer(
            parameters,
            self.INPUT_MNT,
            context
        )
        # If source was not found, throw an exception
        if source_MNT is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.source_MNT))
        
        fields = QgsFields()
        for field in [QgsField("RTSS", QVariant.String)]:
            fields.append(field)
                        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineStringZ,
            source_MNT.crs()
        )
        
        # Send some information to the user
        feedback.pushInfo('================ Information ================')
        feedback.pushInfo('Le CRS de la couche des RTSS est {}'.format(source_RTSS.sourceCrs().authid()))
        feedback.pushInfo('Le CRS du MNT est {}'.format(source_MNT.crs().authid()))

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            
        feedback.pushInfo('Le CRS en sortie est {}'.format(source_MNT.crs().authid()))
        
        # Projection
        layer_rtss_crs = QgsCoordinateReferenceSystem(source_RTSS.sourceCrs().authid())
        layer_mnt_crs = QgsCoordinateReferenceSystem(source_MNT.crs().authid())
        crs_transform = QgsCoordinateTransform(layer_rtss_crs, layer_mnt_crs, QgsProject.instance())
        
        field_names = [field.name() for field in source_RTSS.fields()]
        get_num_rtss = True
        # Verifier si le champs le RTSS existe
        if not field_rtss in field_names:
            get_num_rtss = False
            feedback.pushInfo("Le champs du numéro de rtss n'est pas valide")
        
        feature_count = source_RTSS.featureCount()
        pourc_par_rtss = 100/feature_count
        [feedback.pushInfo("") for j in range(2)]
        feedback.pushInfo('================ Processing ================')
        # Parcourir toute les RTSS
        for i, rtss in enumerate(source_RTSS.getFeatures()):
            # Check cancel
            if feedback.isCanceled():
                break
            # Determiner le numéro de RTSS
            num_rtss = i
            if get_num_rtss:
                num_rtss = rtss[field_rtss]
            feedback.pushInfo("Interpoler le rtss %s..." % num_rtss)
            
            rtss_geom = rtss.geometry()
            if interval_dist != 0:
                rtss_geom = rtss.geometry().densifyByDistance(interval_dist)
        
            stop_rtss = False
            list_point = []
            for vertex in rtss_geom.vertices():
                pt_transform = QgsPointXY(vertex.x(), vertex.y())
                if layer_rtss_crs != layer_mnt_crs:
                    pt_transform = crs_transform.transform(pt_transform)
                
                ident = source_MNT.dataProvider().identify(pt_transform, QgsRaster.IdentifyFormatValue)
                if ident.isValid():
                    if ident.results()[1]:
                        ptz = QgsPoint(pt_transform)
                        ptz.addZValue(ident.results()[1])
                        list_point.append(ptz)
                    else:
                        stop_rtss = True
                        break
                else:
                    stop_rtss = True
                    break
            
            if not stop_rtss:
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolyline(list_point))
                feat.setAttributes([num_rtss])
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
                feedback.pushInfo("Le rtss %s a été ajouter avec succès!" % num_rtss)
            
            else:
                feedback.reportError("ATTENTION! - Le rtss %s n'a pas été interpolé!" % num_rtss)
            
            feedback.setProgressText('%s sur %s rtss d\'intepolé' % (i+1, feature_count))
            progress = (i*pourc_par_rtss)
            if progress > 100: progress = 100
            feedback.setProgress(progress)
        
        [feedback.pushInfo("") for j in range(2)]
        
        return {self.OUTPUT: dest_id}