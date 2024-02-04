
# import libraries
import spacy
from spacy.tokens.doc import Doc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import math

# import local files
from src.features.int_det import setup

# Reference:
# Stanza: https://stanfordnlp.github.io/stanza/

class InteractionDetection:
    def __init__(self,
                 spacy_nlp: dict[int: spacy.language.Language],
                 spacy_doc: dict[int: Doc],
                 unit_size_percentile: float = 0.05
                 ) -> None:
        """
        :param spacy_nlp: spacy.language.Language object of a text
        :param spacy_doc: spacy.tokens.doc.Doc object of a text
        :param unit_size_percentile: the relative sentence size of each narrative unit against the number of tokens of
        the whole text. The smaller the better, since the large unit size may overlook quick change in sentiment in the
        story.
        """

        # self.ann = setup.initServer(text)
        self.nlps = spacy_nlp
        self.docs = spacy_doc
        self.narrative_units = self.initialize_narrative_units(unit_size_percentile)
        self.polarities = None

    def initialize_narrative_units(self, unit_size_percentile: float):
        narrative_units = dict()

        all_token_num = 0
        for doc in self.docs.values():
            all_token_num += len(doc)
        each_unit_token_num = math.ceil(all_token_num * unit_size_percentile)

        # index of each narrative unit
        unit_idx = 0
        # separate token index is necessary to keep track of the number of tokens across different Doc objects
        sent_idx = 0
        # string object that stores the actual text of each narrative unit
        narrative = ''

        for doc in enumerate(self.docs.values()):
            doc: Doc
            for sent in doc.sents:
                sent_idx += 1
                narrative += sent.text + " "
                if sent_idx == each_unit_token_num:
                    narrative_units[unit_idx] = narrative
                    narrative = ""
                    unit_idx += 1
        # add the last remaining sentences to the dictionary
        narrative_units[unit_idx] = narrative
        return narrative_units

    def get_coref_stanfordCoreNLP(self):
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

    def get_coref_spacy(self) -> list[list[spacy.tokens.token.Token]]:
        """
        Get coreference resolution using spacy Coreference Resolver
        :return: list[spacy.Token]
        """
        return

    def analyze_sentiment(self) -> dict[int: dict[str: float]]:
        """
        Return the sentiment of each character
        :return:
        """
        analyzer = SentimentIntensityAnalyzer()
        polarities = dict()
        for idx, text in self.narrative_units.items():
            polarity = analyzer.polarity_scores(text)
            polarities[idx] = polarity
        self.polarities = polarities
        return polarities

    def count_conversation(self):
        pass