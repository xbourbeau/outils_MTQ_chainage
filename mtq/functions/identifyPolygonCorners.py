import numpy as np

def calculate_angle(v1, v2):
    """ Calculate the angle between two vectors v1 and v2 """
    v1_u = v1 / np.linalg.norm(v1)
    v2_u = v2 / np.linalg.norm(v2)
    dot_product = np.dot(v1_u, v2_u)
    angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
    return np.degrees(angle)

def identifyPolygonCorners(vertices, tolerance_angle=170):
    """ 
    Permet de retourner une liste des coordonnées des coins d'un polygon
    Calculate angles at each vertex of a polygon given its vertices and taking only angle smaller than 
    the given tolerance value.

    ** La liste des points ne doit pas avoir de doublon (même pour la fermeture du polygone)
    
    Args:
        vertices (x, y) = Liste de valeur de X et Y des coordonnées du polygon
        tolerance_angle (real) = L'angle en degrees maximum pour être considérer un coin.

    Return: Liste des coordonnées des coins du polygon
    """
    corners = []
    num_vertices = len(vertices)
    
    for i, vertex in enumerate(vertices):
        # Get previous, current, and next vertices
        prev_vertex = vertices[i - 1]
        current_vertex = vertices[i]
        next_vertex = vertices[(i + 1) % num_vertices]  # Wrap around for last vertex
        
        # Vectors between vertices
        v1 = np.array(prev_vertex) - np.array(current_vertex)
        v2 = np.array(next_vertex) - np.array(current_vertex)
        
        # Calculate angle using dot product and arccos
        angle = calculate_angle(v1, v2)
        if angle < tolerance_angle: corners.append(vertex)
        
    return corners