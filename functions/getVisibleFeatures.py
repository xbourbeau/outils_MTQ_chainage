# -*- coding: utf-8 -*-

from qgis.core import QgsRenderContext, QgsFields

''' Méthode de creation d'un itérateur d'entitées visible sur la carte'''
def getVisibleFeatures(layer):
    renderer = layer.renderer().clone()
    ctx = QgsRenderContext()
    renderer.startRender(ctx, QgsFields())
    for feature in layer.getFeatures():
        ctx.expressionContext().setFeature(feature)
        if renderer.willRenderFeature(feature, ctx): yield feature
    renderer.stopRender(ctx)