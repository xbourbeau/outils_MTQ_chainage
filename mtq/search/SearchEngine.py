from typing import Dict

from rapidfuzz import process
from rapidfuzz import fuzz
from rapidfuzz import utils

class SearchEngine:
    
    __slots__ = ("dict_index", "split_word", "dict_facteur_start")

    def __init__(self, dict_index:Dict[str, list[str]]={}, split_word=False):
        """
        Créer le moteur de recherche

        Args:
            dict_index (Dict[str, list[str]]): Le dictionnaire des index de recheche. Ex: Valeur du résultat: [list de recherche]
        """
        self.dict_facteur_start = {1: 8, 2: 5, 3: 3}
        self.updateSearchingIndex(dict_index, split_word)
    
    def updateSearchingIndex(self, dict_index:Dict[str, list[str]], split_word=False):
        """
        Mettre à jour le dictionnaire d'index de recherche

        Args:
            dict_index (Dict[str, list[str]]): Le dictionnaire des index de recheche. Ex: Valeur du résultat: [list de recherche]
        """
        self.setSplitWord(split_word)
        # Index de recherche
        self.dict_index = {}
        # Parcuorir le dictionnaire de recherce
        for key, values in dict_index.items():
            # Parcourir la clée ses valeurs associées
            for text in [key] + list(values):
                if self.splitWord():
                    for mot in text.split(" ") + [text]:
                        # Ajouter chaque valeur servant à la recherche au dictionnaire avec la clé assosier
                        if mot in self.dict_index: self.dict_index[mot].append(key)
                        else: self.dict_index[mot] = [key]
                else:
                    if text in self.dict_index: self.dict_index[text].append(key)
                    else: self.dict_index[text] = [key]

    def setSplitWord(self, split_word):
        self.split_word = split_word

    def searchScore(self, query, choice, **kwargs):
        """
        Méthode pour définir le score de recherche

        Args:
            query (str): Valeur chercher
            choice (str): Valeur comparéer

        Returns: Le score de a quelle point le choix est probable
        """
        # Basic fuzzy match score
        score = fuzz.QRatio(query, choice)
        if score == 0: return 0
        # Boost le score si la recherche match avec le début
        if choice.startswith(query):
            facteur_start = self.dict_facteur_start.get(len(query), 2)
            score *= facteur_start
        # Retourner le score modifier
        return score

    def splitWord(self): return self.split_word

    def fozySearch(self, query):
        return process.extract(query, self.dict_index.keys(), scorer=self.searchScore, limit=1_000, processor=utils.default_process)

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
        for v_match, p_match, idx in self.fozySearch(search_text):
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
