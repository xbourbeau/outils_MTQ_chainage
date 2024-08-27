

def minMaxNormalize(data, min_val=None, max_val=None):
    """
    Permet de normaliser une liste de valeur entre un minimum et un maximum.

    Args:
        data (_type_): La liste de valeurs à normaliser
        min_val (int, optional): Valeur min à utiliser, si None elle est calculer sur la liste. Defaults to None.
        max_val (int, optional): Valeur max à utiliser, si None elle est calculer sur la liste. Defaults to None.

    Returns liste of values between 0 and 1
    """
    # Définir les valeurs min et max selon les paramètres
    min_val = min(data) if min_val is None else min_val
    max_val = max(data) if max_val is None else max_val
    normalized_data = []
    # Parcourir les valeurs de la liste
    for x in data:
        # Ajouter directement le maximum si la valeur est plus grande 
        if x >= max_val: normalized_data.append(1)
        # Ajouter directement le minimum si la valeur est plus petite 
        elif x <= min_val: normalized_data.append(0)
        # Ajouter la valeur normalizé
        else:normalized_data.append((x - min_val) / (max_val - min_val))
    
    return normalized_data