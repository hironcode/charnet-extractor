import networkx as nx
from src.tools.character import Character, AllCharacters
from src.tools.narrative_units import NarrativeUnits
from typing import List, Tuple, Dict, Any

import spacy
import numpy as np

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
        for char in self.meta_chars.values():
            self.add_node(char.id)

    def update_edges_from_polarity(self) -> None:
        """
        Update the edges of the graph based on the polarities in the narrative units
        """
        if self.narrative_units.get_property(0, "polarity") is None:
            raise ValueError("The narrative units do not have a polarity property")
        
        char_num = len(self.char_names)
        adj_matrix = np.zeros((char_num, char_num, self.narrative_units.get_property(0, "polarity").shape[0]))   # (num_chars, num_chars, polarity_vector_dimension)
        
        for i in range(len(self.narrative_units)):
            polarity = np.array(self.narrative_units.get_property(i, "polarity"))   # (polarity_vector_dimension,)
            # identify the characters in the narrative unit
            characters = self.narrative_units.get_property(i, 'characters')
            ids = list(set(char.id for char in characters if char.id))
            assert len(polarity) == adj_matrix.shape[2]
            adj_matrix[ids, ids] += polarity
        # after adding all the polarities, get average
        adj_matrix /= len(self.narrative_units)
        
        # add the most probable label to the graph
        adj_matrix = np.argmax(adj_matrix, axis=-1)  # (num_chars, num_chars)
        for i in range(len(self.char_names)):
            for j in range(len(self.char_names)):
                if i != j:
                    if self.id2label is None:
                        self.add_edge(i, j, polarity=adj_matrix[i, j])
                    else:
                        self.add_edge(i, j, polarity=adj_matrix[i, j], label=self.id2label[adj_matrix[i, j]])

        # label info
        # if "finiteautomata/bertweet-base-sentiment-analysis", ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        # if "siebert/sentiment-roberta-large-english", ["POSITIVE", "NEGATIVE"]


def merge(graph: CharNet, occurences: List[List[str]]) -> nx.Graph:
    """
    Merge all occurrences of the same character into one node
    :return: merged graph
    """
    

    """
    for names in occurences:
        # get the most used reference in the story as a representative of the character
        max_occ = 0
        max_name = names[0]
        for name in names:
            char = graph.chars[name]
            if len(char.occurences) > max_occ:
                max_occ = len(char.occurences)
                max_name = char.name
        # merge nodes
        for name in names:
            char = graph.chars[name]
            if char.name != max_name:
                graph = nx.contracted_nodes(graph, max_name, char.name)
    return graph
"""