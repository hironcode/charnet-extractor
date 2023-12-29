import networkx as nx

class CharacterNetwork:

    def __init__(self, chars):
        self.chars = chars
        self.character_network = nx.Graph()
        self.character_subnetworks = {
            name: None for name in list(self.chars.keys())
        }

    def init_subnetworks(self):
        """
        This method initializes a character subnetwork,
        a network of different referents referring to the same character.
        :return:
        """
        pass
