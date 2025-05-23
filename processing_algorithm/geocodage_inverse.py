# -*- coding: utf-8 -*-
# Importation des librairies
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant
from qgis.core import (QgsProcessing,
                       QgsFeature,
                       QgsField,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsWkbTypes,
                       QgsProcessingParameterFeatureSink)

from ..mtq.core import Geocodage, Chainage

# Fonction qui ajoute les champs requis en fonction des paramètres choisis et du type de géométrie
def addFieldstoSink(data, field_list, offset, format_chainage, precision):
    # Définir le type du champ de chainage à utiliser
    if format_chainage: type_chainage = QVariant.String
    elif precision <= 0: type_chainage = QVariant.Int
    else: type_chainage = QVariant.Double
    
    # Définir les sufixs pour le début/fin ou pour les points
    if data.wkbType() == QgsWkbTypes.Point: sufixs = [""]
    elif data.wkbType() == QgsWkbTypes.LineString: sufixs = ["_debut", "_fin"]
    
    # Liste des noms et type de champ à ajouter 
    champs = [["rtss", QVariant.String], ["chainage", type_chainage]]
    if offset: champs.append(["offset", QVariant.Double])
    
    # Ajouter toutes les champs avec les sufixs et type selectionné
    for sufix in sufixs:
        for name, type in champs:
            # S'asurer que le nom de champ est unique
            if not field_list.append(QgsField(f"{name}{sufix}", type)):
                i = 1
                while field_list.append(QgsField(f"{name}{sufix}_{i}", type)) is False: i += 1
        
    return field_list


class GeocodageInverse(QgsProcessingAlgorithm):

    # Constants
    INPUT = 'INPUT'
    INPUT_RTSS_FIELD = 'INPUT_RTSS_FIELD'
    OUTPUT = 'OUTPUT'
    LAYER_RTSS = 'LAYER_RTSS'
    RTSS = 'RTSS'
    LONG = 'LONG'
    PRECISION = 'PRECISION'
    OFFSET = 'OFFSET'
    FORMATER_RTSS = 'FORMATER_RTSS'
    FORMATER_CHAINAGE = 'FORMATER_CHAINAGE'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GeocodageInverse()

    def name(self):
        return 'geocodageinverse'

    def displayName(self):
        return self.tr('Géocoder (inverse)')

    def group(self):
        return self.tr('RTSS')

    def groupId(self):
        return 'rtss'
    
    def helpUrl(self):
        return "file://sstao00-adm005/TridentAnalyst/Plugin_chainage_mtq/Documentation/Index.html#subsection4-4"
    
    def shortHelpString(self):
        return self.tr(
            '''L'algorithme suivant permet de calculer le RTSS, le chainage et la distance trace le plus proche de chaque entité d'une couche de points ou de lignes.\n'''
            '''Pour les couches de type linéaire, les valeurs sont calculées pour les 2 extrémités de la ligne. '''
            '''Dans le cas où l'extrémité d'une ligne serait positionnée à la fois sur la fin d'un RTSS et au début d'un autre RTSS, '''
            '''le RTSS le plus proche sera déterminé en fonction de la position du point suivant. '''
            '''Cependant, il est possible de définir un champ contenant les valeurs de RTSS des entités si ceux-ci sont déjà connus.\n\n'''
            '''**L'algorithme ne traite pas les couches de types multiples (multipoints ou multilignes). '''
            '''Il faut donc convertir les couches avant de pouvoir les traiter.\n\n\n\n'''
            '''Remerciement: Kevin Therrien''')

    def initAlgorithm(self, config=None):

        # Définition de l'input
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Couche à traiter'),
                [QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine]
            )
        )
        # Paramètre du champ contenant les numéros de RTSS s'il sont connu
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_RTSS_FIELD,
                self.tr("   Champ contenant les numéros de RTSS s'il sont connu"),
                None,
                self.tr(self.INPUT),
                QgsProcessingParameterField.String,
                optional=True
            )
        )
        
        # Définition de la couche RTSS
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LAYER_RTSS,
                self.tr('\nCouche de RTSS pour le module de géocodage'),
                [QgsProcessing.TypeVectorLine],
                'BGR - RTSS'
            )
        )
        # Paramètre du champ de numéro de RTSS
        self.addParameter(
            QgsProcessingParameterField(
                self.RTSS,
                self.tr('   Numéro de RTSS'),
                'num_rts',
                self.tr(self.LAYER_RTSS),
                QgsProcessingParameterField.String
            )
        )
        # Paramètre du chainage de fin du RTSS
        self.addParameter(
            QgsProcessingParameterField(
                self.LONG,
                self.tr('   Chainage de fin des RTSS'),
                'val_longr_sous_route',
                self.tr(self.LAYER_RTSS),
                QgsProcessingParameterField.Numeric
            )
        )
        # Paramètre de la précision du module de géocodage à utiliser
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PRECISION,
                self.tr('   Précision des chainages à géocoder'),
                defaultValue=0,
                minValue=-5,
                maxValue=5
            )
        )
        
        # Paramètre booléen pour formater le numéro de RTSS
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FORMATER_RTSS,
                self.tr('Activer le formatage du RTSS (00000-00-000-0000)'),
                defaultValue=False
            )
        )
        # Paramètre booléen pour formater le chainage
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FORMATER_CHAINAGE,
                self.tr('Activer le formatage du chainage (0+000)'),
                defaultValue=False
            )
        )
        # Paramètre booléen pour calculer l'offset
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OFFSET,
                self.tr('Calculer les décalages par rapport au RTSS'),
                defaultValue=False
            )
        )
        # Définition de l'output
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Couche géocodée')
            )
        )
        
    """ ****************************************** Traitement ****************************************************** """
    def processAlgorithm(self, parameters, context, feedback):
        
        # Définition de la couche en entrée
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None: raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        # Champ opionnel des RTSS s'il sont connue
        champ_input_rtss = self.parameterAsString(parameters, self.INPUT_RTSS_FIELD, context)
        # Ignorer les mulilignes
        if source.wkbType() == QgsWkbTypes.MultiLineString or source.wkbType() == QgsWkbTypes.MultiPoint:
            raise QgsProcessingException("L'algorithme ne peut pas traiter les couches de type Multiple, veuillez la convertir géometrie simple.")
        
        # Définir les intrants
        source_rtss = self.parameterAsVectorLayer(parameters, self.LAYER_RTSS, context)
        if not source_rtss: raise QgsProcessingException(self.invalidSourceError(parameters, self.LAYER_RTSS))
        champ_rtss = self.parameterAsString(parameters, self.RTSS, context)
        champ_chainage = self.parameterAsString(parameters, self.LONG, context)
        precision = self.parameterAsInt(parameters, self.PRECISION, context)
        
        # Définiton des paramètres booléens choisis pour le calcul
        format_rtss = self.parameterAsBool(parameters, self.FORMATER_RTSS, context)
        format_chainage = self.parameterAsBool(parameters, self.FORMATER_CHAINAGE, context)
        offset_val = self.parameterAsBool(parameters, self.OFFSET, context)
        
        
        feedback.pushInfo("")
        feedback.pushInfo("******************** Module de géocodage *******************************")
        # Définir le module de géocodage
        geocode = Geocodage.fromLayer(source_rtss, champ_rtss, champ_chainage, precision=precision)
        feedback.pushInfo(str(geocode.getEpsg()))
        feedback.pushInfo(f"Nombre de RTSS: {len(geocode.getListRTSS())}")
        feedback.pushInfo(f"Précision des chainages: {geocode.precision} (ex: {Chainage.formaterChainage(10**(geocode.precision*-1))})")
        feedback.pushInfo("***************************************************")
        feedback.pushInfo("")
        
        # Ajout des nouveaux champs à la couche en sortie
        output_fields = addFieldstoSink(source, source.fields(), offset_val, format_chainage, precision)
        # Définition du sink
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            output_fields, source.wkbType(), source.sourceCrs())
        
        feedback.pushInfo("Débuter le géocodage inverse...")
        # Création des features à ajouter au sink
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        feedback.pushInfo(f"Nombre d'entitées à géocodée: {source.featureCount()}")
        for current, feat in enumerate(source.getFeatures()):
            # Création de nouveaux features qui peuvent recevoir les valeurs calculées
            new_feat = QgsFeature(output_fields)
            # Ajout des géométries aux nouveaux features
            new_feat.setGeometry(feat.geometry())
            # Liste pour contenir les champs des nouveaux features
            atts = [feat[field.name()] for field in feat.fields()]
            
            rtss = None
            # Définir le RTSS par défault de l'entité
            if champ_input_rtss:
                feat_rtss = geocode.get(str(feat[champ_input_rtss]))
                if feat_rtss is None: feedback.pushWarning(f"Le RTSS ({feat[champ_input_rtss]}) de l'entitée {feat.id()} n'est pas valide")
                else: rtss = feat_rtss.getRTSS()
            
            try:
                # Géocodage pour une couche de point
                if source.wkbType() == QgsWkbTypes.Point:
                    # Géocodage inverse
                    result = geocode.geocoderInversePoint(feat.geometry(), rtss=rtss)
                    # Ajout des valeurs attributaires calculées
                    atts.append(result.getRTSS().value(format_rtss))
                    atts.append(result.getChainage().value(format_chainage, precision=precision))
                    if offset_val: atts.append(result.getOffset())
                    
                # Géocodage pour une couche de ligne
                elif source.wkbType() == QgsWkbTypes.LineString:
                    points = feat.geometry().asPolyline()
                    # Géocodage inverse le premier point
                    result_1 = geocode.geocoderInversePoint(points[0], rtss=rtss)
                    # Géocodage inverse le dernier point
                    result_2 = geocode.geocoderInversePoint(points[-1], rtss=rtss)

                    # Géocodage inverse
                    # Ajout des valeurs attributaires calculées
                    atts.append(result_1.getRTSS().value(format_rtss))
                    atts.append(result_1.getChainage().value(format_chainage, precision=precision))
                    if offset_val: atts.append(result_1.getOffset())

                    atts.append(result_2.getRTSS().value(format_rtss))
                    atts.append(result_2.getChainage().value(format_chainage, precision=precision))
                    if offset_val: atts.append(result_2.getOffset())
            # Informer l'utilisateur s'il y a un problème avec le géocodage inverse de l'entitée
            except: feedback.pushWarning(f"L'entitée {feat.id()} n'a pas été géocodée correctement")
                
            # Ajout des valeurs attributaires aux features
            new_feat.setAttributes(atts)
            # Ajout du feature au sink
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
            
            # Arrêter l'algorithme si le processus est annulé
            if feedback.isCanceled(): break
            # Barre de progression
            feedback.setProgress(int(current * total))
            
        # Affichage des résultats
        return {self.OUTPUT: dest_id}
