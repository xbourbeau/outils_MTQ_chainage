from typing import Dict
from .fuzzywuzzy import process
from .fuzzywuzzy import fuzz

class SearchEngine:
    
    __slots__ = ("dict_index")

    def __init__(self, dict_index:Dict[str, list[str]]={}):
        """
        Créer le moteur de recherche

        Args:
            dict_index (Dict[str, list[str]]): Le dictionnaire des index de recheche. Ex: Valeur du résultat: [list de recherche]
        """
        self.updateSearchingIndex(dict_index)
    
    def updateSearchingIndex(self, dict_index:Dict[str, list[str]]):
        """
        Mettre à jour le dictionnaire d'index de recherche

        Args:
            dict_index (Dict[str, list[str]]): Le dictionnaire des index de recheche. Ex: Valeur du résultat: [list de recherche]
        """
        # Index de recherche
        self.dict_index = {}
        # Liste des clées du dictionnaire
        #self.list_of_keys = [k.lower() for k in dict_index.keys()]
        # Parcuorir le dictionnaire de recherce
        for key, values in dict_index.items():
            # Parcourir la clée ses valeurs associées
            for text in [key] + list(values):
                for mot in text.split(" "):
                    # Ajouter chaque valeur servant à la recherche au dictionnaire avec la clé assosier
                    if mot in self.dict_index: self.dict_index[mot].append(key)
                    else: self.dict_index[mot] = [key]

    def searchScore(self, query, choice):
        """
        Méthode pour définir le score de recherche

        Args:
            query (str): Valeur chercher
            choice (str): Valeur comparéer

        Returns: Le score de a quelle point le choix est probable
        """
        # Basic fuzzy match score
        score = fuzz.ratio(query, choice)
        len_score = len(query)

        if len_score == 1: facteur_start = 8
        elif len_score == 2: facteur_start = 5
        elif len_score == 3: facteur_start = 2
        else: facteur_start = 1
        # Boost le score si la recherche match avec le début
        if choice.startswith(query): score *= facteur_start
        # Boost le score si la valeur comparer est une clée du dictionnaire
        #if choice in self.list_of_keys: score *= 1.2
        # Retourner le score modifier
        return score

    def fozySearch(self, query):
        return process.extract(query, self.dict_index.keys(), scorer=self.searchScore, limit=1_000)

    def search(self, search_text:str, limit=1_000, min_score=25):
        """
        Permet d'éffectuer une recherche

        Args:
            query (str): Le texte à chercher
            limit (int, optional): Le nombre maximum de valeur de retour. Defaults to 1_000.
            min_score (int, optional): _description_. Defaults to 25.

        Returns (list[str]): La list ordonnée des éléments le plus probalble de la recherhe
        """
        # Compteur du nombre d'élément trouvé
        count = 0
        # Indicateur que la recheche est complété
        stop_search = False
        if len(search_text) > 5: min_score += 35
        elif len(search_text) > 2: min_score += 25
        # Liste des résultats de recheche et des clées trouvée
        search_result = {}
        # Parcourir les valeurs et son score pour le texte de recheche 
        for v_match, p_match in self.fozySearch(search_text):
            # Vérifier si le score est plus petit que le score min
            if not stop_search: stop_search = p_match < min_score
            # Parcourir les clées possible pour la recherche
            for key in self.dict_index.get(v_match):
                # Continuer seulement si la clée n'est pas déjà dans le résultat
                if key in search_result:
                    if search_result[key] < p_match: search_result[key] = p_match
                else:
                    # Ajouter la clée et le score au dictionnaire des résultats 
                    search_result[key] = p_match
                    count += 1
                    if not stop_search: stop_search = count >= limit 
                if stop_search: break
            if stop_search: break
        # Retourner la liste de clé en ordre de score
        return [i for i, j in sorted(search_result.items(), key=lambda item: item[1], reverse=True)]
