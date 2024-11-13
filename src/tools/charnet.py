import networkx as nx
from src.tools.character import Character, AllCharacters
from src.tools.narrative_units import NarrativeUnits
from typing import List, Tuple, Dict, Any

import spacy
import numpy as np
import torch
import torch.nn.functional as F

class CharNet(nx.Graph):
    def __init__(self,
                 title: str,
                 type: str,
                 chars: AllCharacters,
                 narrative_units: NarrativeUnits,
                 id2label: Dict[int, str]=None,
                 ) -> None:
        """
        :param occurrences: a list of different references to the same characters
        :param title: title of the story
        :param type: type of the character network: "co-occurrence" or "conversation"
        :param chars: AllCharacters object that contains all the characters in the story
        :param narrative_units: NarrativeUnits object that contains the story
        :param id2label: dictionary that maps the label id to the label name
        """
        super().__init__(name=title, type=type)
        self.type = type
        self.meta_chars = chars
        self.char_names = chars.get_names()
        self._charname_id = {char.id: char.name for char in chars.get_all_characters()}
        self.narrative_units = narrative_units
        self.id2label = id2label

        self.update_nodes_from_metachars()

    def rewrite_metachars_from_dict(self, meta_chars: dict[str: Character], update_graph:bool=True) -> None:
        """
        Rewrite the metachars dictionary and update the charname_id dictionary
        :param meta_chars: dictionary of character names and their corresponding Character objects
        """

        self.meta_chars = meta_chars
        # update the charname_id dictionary
        self._charname_id = {char.id: name for name, char in meta_chars.items()}
        if update_graph:
            self.update_nodes_from_metachars()

    def update_metachars_each(self, name:str, character: Character) -> None:
        self.meta_chars[name] = character

    def update_nodes_from_metachars(self) -> None:
        """
        Update the graph from the metachars dictionary already registered in this instance
        """
        self.clear()
        for char in self.meta_chars.get_all_characters():
            self.add_node(char.id)

    def update_edges_from_polarity(self) -> None:
        """
        Update the edges of the graph based on the polarities in the narrative units
        """
        if self.narrative_units.get_property(0, "polarity") is None:
            raise ValueError("The narrative units do not have a polarity property")
        
        char_num = len(self.char_names)
        adj_matrix = np.zeros((char_num, char_num, self.narrative_units.get_property(0, "polarity").shape[0]))   # (num_chars, num_chars, polarity_vector_dimension)

        # to mask the pairs of characters whose polarity has not been updated
        not_updated = np.full(adj_matrix.shape[:2], True, dtype=bool)   # (num_chars, num_chars)

        for i in range(len(self.narrative_units)):
            polarity = np.array(self.narrative_units.get_property(i, "polarity"))   # (polarity_vector_dimension,)
            # identify the characters in the narrative unit
            characters = self.narrative_units.get_property(i, 'characters')
            ids = list(set(char.id for char in characters if char.id))
            assert len(polarity) == adj_matrix.shape[2]
            # Create indeces such that all the interactions among characters given with the ids
            # will be updated with the polarity
            grid = np.ix_(ids, ids)
            adj_matrix[grid] += polarity
            not_updated[grid] = False

        # after adding all the polarities, get average
        adj_matrix /= len(self.narrative_units)

        # select the most probable labels with softmax
        adj_matrix = F.softmax(torch.Tensor(adj_matrix)).argmax(dim=-1).numpy() # (num_chars, num_chars)

        # mask non-updated pairs
        adj_matrix[not_updated] = -100

        for i in range(char_num):
            for j in range(char_num):
                # rule out the self-loops and the non-updated pairs
                if i != j and adj_matrix[i, j] != -100:
                    value = adj_matrix[i, j]
                    if self.id2label is None:
                        self.add_edge(i, j, polarity=value)
                    else:
                        self.add_edge(i, j, polarity=value, label=self.id2label[value])

        # label info
        # if "finiteautomata/bertweet-base-sentiment-analysis", ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        # if "siebert/sentiment-roberta-large-english", ["POSITIVE", "NEGATIVE"]
        

def merge_charnet_occurences(graph: CharNet) -> nx.Graph:
    """
    Merge all occurrences of the same character into one node
    :return: merged graph
    """
    occurences: np.ndarray = graph.meta_chars.occurences
    same_idxs = np.where(occurences == 1)
    idxs = [list(map(int, mulidx)) for mulidx in zip(*same_idxs)]
    for same_char_ids in idxs:
        # get the most used reference in the story as a representative of the character
        max_occ = 0
        max_id = same_char_ids[0]
        for id in same_char_ids:
            char:Character = graph.meta_chars.id_chars[id]
            if len(char.occurences) > max_occ:
                max_occ = len(char.occurences)
                max_id = char.id
        # merge nodes
        for id in same_char_ids:
            char:Character = graph.meta_chars.id_chars[id]
            if char.id != max_id:
                graph = nx.contracted_nodes(graph, max_id, char.id, self_loops=False)
    return graph
