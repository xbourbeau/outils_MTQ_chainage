def getMinOffset(offsets:list):
    """
    Permet de retourner le offset le plus proche de 0 d'une liste

    Args:
        offsets (list): Liste des offsets à comparer

    Return: La valeur de la list le plus proche de 0 
    """
    # Check if the list is empty
    if not offsets: return None
    # Use the min function with a custom key to find the closest value to 0
    return min(offsets, key=lambda x: abs(x))