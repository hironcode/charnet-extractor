
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
                 spacy_nlps: dict[int: spacy.language.Language],
                 spacy_docs: dict[int: Doc],
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
        self.nlps = spacy_nlps
        self.docs = spacy_docs
        self.narrative_units = self.initialize_narrative_units(unit_size_percentile, self.docs)
        self.nlp_coref = self.initialize_coref_resolution(None)
        self.polarities = None

    def initialize_narrative_units(self,
                                   unit_size_percentile: float,
                                   docs: dict[int: Doc]
                                   ) -> dict[int: spacy.language.Language]:
        narrative_units = dict()

        # calculate the total number of tokens in the text
        all_token_num = 0
        for doc in docs.values():
            all_token_num += len(doc)
        # calculate the number of tokens for each narrative unit
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

    def initialize_coref_resolution(self, nlps: dict[int: spacy.language.Language]) -> spacy.language.Language:
        nlp_coref = spacy.load("en_coreference_web_trf")

        # use replace_list to replace the coref clusters with the head of the cluster
        nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
        nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])

        # we won't copy over the span cleaner
        nlp.add_pipe("coref", source=nlp_coref)
        nlp.add_pipe("span_resolver", source=nlp_coref)
        return nlp

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