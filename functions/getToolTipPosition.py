# -*- coding: utf-8 -*-

def getToolTipPosition(mouse_point, text_a_afficher, angle):
    """
    Fonction qui permet de retourner la postion du ToolTip dans la carte
    selon la taille du texte et l'angle de la route

    Args:
        mouse_point (QPoint): La position de la souris
        text_a_afficher (str): Le text du tooltip
        angle (real): L'angle du RTSS

    Returns:
        list: liste du X et Y de la position de la souris
    """
    if angle >= 180: angle -= 180
    if angle > 90:
        x = mouse_point.x() + 8
        y = mouse_point.y() - len(text_a_afficher) * 20
    else:
        x = mouse_point.x() + 8
        y = mouse_point.y() + len(text_a_afficher)
        
    return (x, y)