def getMaxOffset(offsets:list):
    """
    Permet de retourner le offset le plus loin de 0 d'une liste

    Args:
        offsets (list): Liste des offsets à comparer

    Return: La valeur de la list le plus loin de 0 
    """
    # Check if the list is empty
    if not offsets: return None
    # Use the min function with a custom key to find the closest value to 0
    return max(offsets, key=lambda x: abs(x))