
# import libraries
import spacy
from spacy.tokens.doc import Doc

# import local files
from src.features.int_det import setup

# Reference:
# Stanza: https://stanfordnlp.github.io/stanza/

class InteractionDetection:
    def __init__(self, spacy_nlp: spacy.language.Language, spacy_doc: Doc, text):
        self.ann = setup.initServer(text)
        self.nlp = spacy_nlp
        self.doc = spacy_doc
        # because of the StanfordCoreNLP capacity problem and for narrative-unit-based sentiment analysis,
        # butch processing is needed

    def get_coref(self):
        # reference:
        # https://stackoverflow.com/questions/62735456/understanding-and-using-coreference-resolution-stanford-nlp-tool-in-python-3-7
        chain = self.ann.corefChain
        print(type(chain))
        print(dict(chain))
        chain_dict = {}
        for chain_idx, chain in enumerate(chain):
            chain_dict[chain_idx] = {}
            chain_dict[chain_idx]['chainID'] = chain.chainID
            chain_dict[chain_idx]['mentions'] = [{'mentionID': mention.mentionID,
                                                  'beginIndex': mention.beginIndex,
                                                  'endIndex': mention.endIndex,
                                                  'sentenceIndex': mention.sentenceIndex,
                                                  'ref': '',
                                                  } for mention in chain.mention]

        for k, coreference in chain_dict.items():
            ref_list = []
            for i, mention in enumerate(coreference['mentions']):
                ref = self.ann.sentence[mention['sentenceIndex']].token[mention['beginIndex']:mention['endIndex']]
                ref = ' '.join(t.word for t in ref)
                chain_dict[k]['mentions'][i]['ref'] = ref
                ref_list.append({
                    'beginIndex': mention['beginIndex'],
                    'endIndex': mention['endIndex'],
                })
            chain_dict[k]['coreferences'] = ref_list
        return chain_dict

    def analyze_sentiment(self):
        """
        Return the sentiment of each character
        :return:
        """