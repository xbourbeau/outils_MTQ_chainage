# -*- coding: utf-8 -*-


def getToolTipPosition(mouse_point, text_a_afficher, angle):
    if angle >= 180: angle -= 180
    if angle > 90:
        x = mouse_point.x() + 8
        y = mouse_point.y() - len(text_a_afficher) * 20
    else:
        x = mouse_point.x() + 8
        y = mouse_point.y() + len(text_a_afficher)
        
    return (x, y)