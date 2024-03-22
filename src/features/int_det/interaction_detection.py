# import libraries
import spacy
from spacy.tokens.doc import Doc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import math
from collections import defaultdict
from spacy.matcher import Matcher
import json
from wasabi import msg

# import local files
from src.features.int_det import setup
import src.tools.character
from src.tools.path_tools import PathTools


# Reference:
# Stanza: https://stanfordnlp.github.io/stanza/

class InteractionDetection:
    def __init__(self,
                 title: str,
                 spacy_nlp: spacy.language.Language,
                 spacy_docs: dict[int: Doc],
                 chars: dict[str: src.tools.character.Character],
                 unit_size_percentile: float = 0.05,
                 ) -> None:
        """
        :param spacy_nlp: spacy.language.Language object of a text
        :param spacy_doc: spacy.tokens.doc.Doc object of a text
        :param unit_size_percentile: the relative sentence size of each narrative unit against the number of tokens of
        the whole text. The smaller the better, since the large unit size may overlook quick change in sentiment in the
        story.
        :param chars: a dictionary of character names and Character objects
        """

        # self.ann = setup.initServer(text)
        self.title = title
        self.nlps = spacy_nlp
        self.docs = spacy_docs
        self.unit_size_percentile = unit_size_percentile
        self.polarities = None
        self.chars = chars
        self.narrative_units = None

    def run(self):
        # initialize the narrative units
        narrative_units = self.initialize_narrative_units(self.unit_size_percentile, self.docs)

        # create a nlp object for coreference resolution
        nlp_coref = self.initialize_coref_resolution()

        # get clusters for each narrative unit
        narrative_units_w_clusters = self.get_coref_spacy(narrative_units, nlp_coref)

        # get polarity of each narrative unit
        narrative_units_w_clusters_polarity = self.analyze_sentiment(narrative_units_w_clusters)

        # conversation

    def initialize_narrative_units(self,
                                   unit_size_percentile: float,
                                   docs: dict[int: Doc]
                                   ) -> defaultdict[int: dict[str: str]]:
        narrative_units = defaultdict(dict)

        # calculate the total number of tokens in the text
        all_sent_num = 0
        for doc in docs.values():
            all_sent_num += len(list(doc.sents))
        # calculate the number of tokens for each narrative unit
        each_unit_sent_num = math.ceil(all_sent_num * unit_size_percentile)

        # index of each narrative unit
        unit_idx = 0
        # separate token index is necessary to keep track of the number of tokens across different Doc objects
        sent_idx = 0
        # string object that stores the actual text of each narrative unit
        narrative = ''

        for doc in self.docs.values():
            doc: Doc
            for sent in doc.sents:
                sent_idx += 1
                narrative += sent.text + " "
                if sent_idx == each_unit_sent_num:
                    # add the narrative-unit text to the dictionary
                    narrative_units[unit_idx]["text"] = narrative
                    narrative = ""
                    unit_idx += 1
                    sent_idx = 0
        # add the last remaining sentences to the dictionary
        narrative_units[unit_idx]["text"] = narrative
        self.narrative_units = narrative_units
        return narrative_units

    def initialize_coref_resolution(self, narrative_units=None) -> spacy.language.Language:
        """for i in range(len(narrative_units)):
            nlp_coref = spacy.load("en_coreference_web_trf")
            nlp = spacy.load("en_core_web_trf")

            # use replace_list to replace the coref clusters with the head of the cluster
            nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
            nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])

            # we won't copy over the span cleaner
            nlp.add_pipe("coref", source=nlp_coref)
            nlp.add_pipe("span_resolver", source=nlp_coref)
            narrative_units[i]["nlp_coref"] = nlp_coref
        return narrative_units"""

        nlp_coref = spacy.load("en_coreference_web_trf")
        nlp = spacy.load("en_core_web_trf")

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

    def get_coref_spacy(self,
                        narrative_units: defaultdict[int: dict],
                        nlp_coref: spacy.language.Language,
                        ) -> defaultdict[int: dict[str: dict[str: list[str]]]]:
        """
        Get coreference resolution using spacy Coreference Resolver
        :return: list[spacy.Token]
        """

        # for each narrative unit, get the text and get the coreference clusters
        for i in range(len(narrative_units)):
            text = narrative_units[i]["text"]
            doc = nlp_coref(text)
            # for each cluster, get mentions and their start and end indices, entity types, and dependency labels
            clusters = dict()
            # clusters = {cluster_idx: {
            #     mention.text: {
            #         "start": mention.start,
            #         "end": mention.end,
            #         "ent_type_": [tok.ent_type_ for tok in mention],
            #         "dep_": [tok.dep_ for tok in mention],
            #     }
            # } for cluster_idx, cluster in doc.spans.items() for mention in cluster}
            for cluster_idx, cluster in doc.spans.items():
                clusters[cluster_idx] = dict()
                for mention in cluster:
                    clusters[cluster_idx][mention.text] = {
                        "start": mention.start,
                        "end": mention.end,
                        "ent_type_": [tok.ent_type_ for tok in mention],
                        "dep_": [tok.dep_ for tok in mention],
                    }

            msg.good(f"Coref resolution for unit{i} is done.\n"
                     f"Number of clusters: {len(clusters)}\n")
            for cluster_idx, cluster in clusters.items():
                print(f"{cluster_idx}: {cluster}")

            cleaned = self._clean_coref(clusters)
            msg.good(f"Coref resolution cleaning for unit{i} is done.\n"
                     f"Number of cleaned clusters: {len(cleaned)}\n")
            for cluster_idx, cluster in cleaned.items():
                print(f"{cluster_idx}: {cluster}")

            narrative_units[i]["clusters"] = cleaned
        self.narrative_units = narrative_units
        return narrative_units

    def _clean_coref(self, clusters: dict[int: dict[str: dict[str]]]):
        """
        Clean the coreference clusters by removing unnecessary detected coreferences
        :param clusters:
        :return:
        """
        cleaned_clusters = dict()
        for label, mentions in clusters.items():
            # filter out clusters named "coref_clusters_#"
            if label.startswith("coref_clusters"):
                continue
            # filter out clusters that do not contain PERSON
            if any(ent == "PERSON" for mention_val in mentions.values() for ent in mention_val['ent_type_']):
                pass
            else:
                continue

            cleaned_mentions = dict()

            # for each mention in a cluster_head_coref, filter out single-word mentions whose
            # dependency label is possessive (i.e. "her" for "her NOUN")
            # because those mentions do not serve as an object
            for mention, mention_val in mentions.items():
                if len(mention) == 1 and mention_val["dep_"][0] == "poss":
                    continue
                cleaned_mentions[mention] = mention_val
            cleaned_clusters[label] = cleaned_mentions
        return cleaned_clusters


    def save(self) -> None:
        """
        Save the (1) entire, (2) narrative units, (3) co-reference, (4) sentiment analysis, and (5) conversation
        :return:
        """
        pt = PathTools()
        st_path = pt.get_target_dir(f"reports/stories/{self.title}")

        # convert the narrative units dictionary to a json file
        with open(st_path.joinpath("narrative_units.json"), "w") as f:
            json.dump(self.narrative_units, f)




    def analyze_sentiment(self, narrative_units) -> defaultdict[int: dict[str: dict[str: float]]]:
        """
        add sentiment polarity to each narrative unit
        :return:
        """
        analyzer = SentimentIntensityAnalyzer()
        polarities = dict()
        for i in range(len(narrative_units)):
            text = narrative_units[i]["text"]
            polarity = analyzer.polarity_scores(text)
            narrative_units[i]["polarity"] = polarity
        return narrative_units

    def detect_conversations(self,
                             narrative_units: defaultdict[int: dict],
                             chars: dict[str: src.tools.character.Character],
                             nlp: spacy.language.Language,
                             doc: spacy.tokens.doc.Doc,
                             ) -> dict[dict[str: str]: int]:
        """
        Detect every conversation in the narrative units
        :param narrative_units: narrative units of the story
        :param chars: dictionary of character names and Character objects
        :param tracker: dictionary whose keys are speaker and lister names and
        :param nlp: spacy language object
        :return:
        """
        matcher = Matcher(nlp.vocab)
        # reference:
        # https://op.europa.eu/en/web/eu-vocabularies/formex/physical-specifications/character-encoding/quotation-marks
        # spacy does not tokenize and single out an apostrophe and Matcher is a token-based algorithm
        # So we do not consider a case where the matcher picks an apostrophe used for a contraction

        quo_start = ["\u0022", "\u0027", "\u0060", "\u00AB", "\u2018", "\u201B", "\u201C", "\u201F", "\u2039"]
        quo_end = ["\u0022", "\u0027", "\u00B4","\u00BB", "\u2019", "\u201A", "\u201D", "\u201E", "\u203A"]
        
        pattern = [
            {"TEXT": {"IN": quo_start}},
            {"IS_ASCII": True, "ORTH": {"NOT_IN": ['']}},
            {"TEXT": {"IN": quo_end}},
        ]
        matcher.add("CONVERSATION", [pattern], greedy="LONGEST")
        for i in range(len(narrative_units)):
            pass

    def count_conversations(self):
        pass
