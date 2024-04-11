# -*- coding: utf-8 -*-
from PyQt5.QtCore import (  QCoreApplication,
                            QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsPointXY,
                       QgsGeometry,
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
                       QgsWkbTypes,
                       NULL)

'''
Fonction qui permet de générer des lignes perpendiculaire à un certain interval le long d'une ligne.
'''
class generatePerpendicularLines(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_LINE = 'INPUT_LINE'
    INPUT_INTERVAL = 'INPUT_INTERVAL'
    INPUT_LINE_LENGTH = 'INPUT_LINE_LENGTH'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return generatePerpendicularLines()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'generatePerpendicularLines'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Générer des lignes perpendiculaire à un interval")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Générale')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'generale'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("L'Agorithme permet de créer des lignes perpendiculaire à un interval donnée")

    def helpUrl(self):
        return "file://sstao00-adm005/TridentAnalyst/Plugin_chainage_mtq/Documentation/Index.html#subsection4-5"

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINE,
                self.tr('Entrée de la couche linéaire'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        parametre_dist = QgsProcessingParameterDistance (
                            self.INPUT_INTERVAL,
                            self.tr('Interval des lignes à générer'),
                            20,
                            minValue=1
                        )
        parametre_dist.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        parametre_dist.setDataType(0) # Nombre entier
        self.addParameter(parametre_dist)
        
        
        parametre_long = QgsProcessingParameterDistance (
                            self.INPUT_LINE_LENGTH,
                            self.tr('Longueur perpendiculaire des lignes à générer'),
                            20,
                            minValue=1
                        )
        parametre_long.setDefaultUnit(QgsUnitTypes.DistanceMeters)
        parametre_long.setDataType(0) # Nombre entier
        self.addParameter(parametre_long)
            
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Interval de lignes perpendiculaires')
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
            self.INPUT_LINE,
            context
        )
        # If source was not found, throw an exception
        if source_RTSS is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LINE))
        
        
        # Aller chercher la valeur de l'interval de distance
        interval_dist = self.parameterAsInt(
            parameters,
            self.INPUT_INTERVAL,
            context
        )
        # Verifier que le paramêtre n'est pas vide
        if not interval_dist:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_INTERVAL))
            
        # Aller chercher la valeur de la longueur des lignes
        longueur_ligne = self.parameterAsInt(
            parameters,
            self.INPUT_LINE_LENGTH,
            context
        )
        # Verifier que le paramêtre n'est pas vide
        if not longueur_ligne:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LINE_LENGTH))    
        
        
        fields = QgsFields()
        for field in [QgsField("id", QVariant.Int),
                        QgsField("pos", QVariant.Int),
                        QgsField("long", QVariant.Int)]:
            fields.append(field)
                        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            source_RTSS.sourceCrs()
        )

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source_RTSS.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source_RTSS.featureCount() if source_RTSS.featureCount() else 0
        features = source_RTSS.getFeatures()
        
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            line_geom = feature.geometry()
            # Longueur géometrique de la ligne
            longueur_geometrique = line_geom.length()
            # Nombre de point à créer sur le RTSS
            longeur_ajuster = int(longueur_geometrique-(longueur_geometrique%interval_dist))
            
            long_gauche = (longueur_ligne/2) * - 1
            long_droite = (longueur_ligne/2)
            
            id = 1
            # Parcourire chaque interval du RTSS
            for dist in range(0, longeur_ajuster+interval_dist, interval_dist):
                                                 
                point_centre = line_geom.interpolate(dist).asPoint()
                point_gauche = self.pointOffset(line_geom, point_centre, long_gauche)
                point_droite = self.pointOffset(line_geom, point_centre, long_droite)
                
                perpendicular_line = QgsGeometry().fromPolylineXY([point_gauche, point_centre, point_droite])
                
                feat = QgsFeature()
                feat.setGeometry(perpendicular_line)
                feat.setAttributes([id, dist, long_droite])
                # Add a feature in the sink
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
                
                id += 1
                
            if int(longueur_geometrique) != longeur_ajuster:
                
                point_centre = line_geom.interpolate(longueur_geometrique).asPoint()
                point_gauche = self.pointOffset(line_geom, point_centre, long_gauche)
                point_droite = self.pointOffset(line_geom, point_centre, long_droite)
                
                perpendicular_line = QgsGeometry().fromPolylineXY([point_gauche, point_centre, point_droite])
                
                feat = QgsFeature()
                feat.setGeometry(perpendicular_line)
                feat.setAttributes([id, longueur_geometrique, long_droite])
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

    def pointOffset(self, line, point, dist):
        DistancePoint = line.lineLocatePoint(QgsGeometry.fromPointXY(point))
        if DistancePoint == 0:
            for idx, vertice in enumerate(line.vertices()):
                if idx == 1:
                    Vertex = vertice
                    break
            length = (((Vertex.x() - point.x())**2)+((Vertex.y() - point.y())**2))**0.5
            ##Coordonnée des points parralèl à la ligne
            xp = point.x() + dist * ((Vertex.y()-point.y()) / length)
            yp = point.y() + dist * ((point.x()-Vertex.x()) / length)
        else:
            DiffMin = 999999
            for vertice in line.vertices():
                DistVertex = line.lineLocatePoint(QgsGeometry.fromPointXY(QgsPointXY(vertice.x(),vertice.y())))
                # La différence de distance entre le point le plus proche sur la ligne du point en entrée et le vertex
                Diff = abs(DistancePoint - DistVertex)
                if Diff < DiffMin and (DistancePoint - DistVertex) > 0:
                    DiffMin = Diff #Nouvelle différence minimum
                    Vertex = QgsPointXY(vertice.x(),vertice.y()) #Garder le verterx
                    
            length = (((Vertex.x() - point.x())**2)+((Vertex.y() - point.y())**2))**0.5
            ##Coordonnée des points parralèl à la ligne
            xp = point.x() + dist * ((point.y()-Vertex.y()) / length)
            yp = point.y() + dist * ((Vertex.x()-point.x()) / length)
        
        return QgsPointXY(xp,yp)