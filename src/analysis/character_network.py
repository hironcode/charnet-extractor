import networkx as nx
from src.tools.character import Character

class CharacterNetwork(nx.Graph):
    def __init__(self,
                 chars: dict[str: Character],
                 occurrences: list[list],
                 interactions: list[list[str, str, int]],    # [char1, char2, weight]
                 title: str,
                 type: str) -> None:
        """
        :param chars: dictionary of character names and their corresponding Character objects
        :param occurrences: a list of different references to the same characters
        :param title: title of the story
        :param type: type of the character network: "co-occurrence" or "conversation"
        """
        super().__init__(name=title, type=type)
        self.type = type
        self.chars = chars
        self.interactions = interactions

    def initialize(self) -> None:
        """
        Initialize the character network based on the provided character list (nodes) and interactions (weighted edges)
        :return:
        """

        id_params = {
            name: char.character_id for name, char in self.chars.items()
        }

        # add nodes
        self.add_nodes_from(self.chars.keys())
        self.add_edges_from(self.interactions)


def merge(graph: CharacterNetwork, occurrences: dict[str: Character]) -> nx.Graph:
    """
    Merge all occurrences of the same character into one node
    :return: merged graph
    """
    for names in occurrences:
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

