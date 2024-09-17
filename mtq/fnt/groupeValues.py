import numpy as np

def groupeValues(values, n_clusters=2):
    """
    Permet de grouper une liste de valeurs similaire avec la méthode K-means.

    Args:
        values: Liste des valeurs à grouper
        n_clusters (int, optional): Le nombre de groupes à faire. Defaults to 2.

    Returns:
        _type_: _description_
    """
    try: from sklearn.cluster import KMeans
    except: return None
    # Reshape the data to a 2D array
    X = np.array(values).reshape(-1, 1)
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X)
    # Get the cluster labels
    return kmeans.labels_