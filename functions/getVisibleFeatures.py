# -*- coding: utf-8 -*-
from qgis.core import QgsRenderContext, QgsFields, QgsVectorLayer

def getVisibleFeatures(layer:QgsVectorLayer):
    ''' Fonction de creation d'un itérateur d'entitées visible sur la carte '''
    renderer = layer.renderer().clone()
    ctx = QgsRenderContext()
    renderer.startRender(ctx, QgsFields())
    for feature in layer.getFeatures():
        ctx.expressionContext().setFeature(feature)
        if renderer.willRenderFeature(feature, ctx): yield feature
    renderer.stopRender(ctx)