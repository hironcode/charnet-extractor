import stanza
from stanza.server import CoreNLPClient
import warnings

# First, please download StanfordNLP to your own local directory
# Refer to this document: https://stanfordnlp.github.io/stanza/client_setup.html

def initServer(text, warning=True):
    if warning:
        warnings.warn("Please download StanfordNLP to your own local directory first. "
                      "Refer to this document: https://stanfordnlp.github.io/stanza/client_setup.html")
    with CoreNLPClient(
            annotators=['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'parse', 'depparse', 'coref'],
            timeout=150000,
            memory='6G') as client:
        ann = client.annotate(text)
        return ann

