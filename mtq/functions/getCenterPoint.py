
def getCenterPoint(coords):
    """
    Permet de retourner les coordonnées du point central entre 2 points.

    Args:
        coords (list): Liste de 1 ou 2 points pour trouver le point milieu.

    Returns: Les coordonnées XY du point milieu.
    """
    if len(coords) == 1: return coords[0]
    elif len(coords) == 2:
        x1, y1 = coords[0]
        x2, y2 = coords[1]

        xm = (x1 + x2) / 2
        ym = (y1 + y2) / 2

        return (xm, ym)
    else: return None