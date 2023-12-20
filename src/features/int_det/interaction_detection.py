
# import libraries
import stanza

# import local files
from src.features.int_det import setup

# Reference:
# Stanza: https://stanfordnlp.github.io/stanza/

class InteractionDetection:
    def __init__(self, text):
        self.ann = setup.initServer(text)

    def coref(self):
        print(self.ann.corefChain)
