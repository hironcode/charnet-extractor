# import libraries
import spacy
from spacy.tokens.doc import Doc
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import math
from collections import defaultdict
from spacy.matcher import Matcher
import json
from wasabi import msg
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from typing import List, Tuple, Dict, Any

# import local files
# from src.features.int_det import setup
from src.tools import narrative_units
from src.tools.character import Character, AllCharacters
from src.tools.path_tools import PathTools


# Reference:
# Stanza: https://stanfordnlp.github.io/stanza/

class InteractionDetection:
    def __init__(self,
                 title: str,
                 spacy_nlp: spacy.language.Language,
                 spacy_docs: dict[int: Doc],
                 chars: AllCharacters,
                 narrative_units: narrative_units.NarrativeUnits,
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
        self.chars = chars
        self.narrative_units = narrative_units
        self.conv_tracker = {}

        self.sentiment_analysis_ml_init = False
    

    def run(self, sentiment_analysis: str="ml", hf_model="finiteautomata/bertweet-base-sentiment-analysis") -> None:
        # create a nlp object for coreference resolution
        # nlp_coref = self.initialize_coref_resolution()

        # get clusters for each narrative unit
        # narrative_units = self.get_coref_spacy(narrative_units, nlp_coref)

        # get polarity of each narrative unit
        if sentiment_analysis == "vader":
            self.narrative_units = self.get_sentiment_vader(self.narrative_units)
        elif sentiment_analysis == "ml":
            self.narrative_units = self.get_sentiment_hugface(self.narrative_units, hf_model)
        else:
            raise ValueError("Invalid sentiment analysis method. Choose 'vader' for rule-based or 'ml' for machine learning-based sentiment analysis.")

        # conversation

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

    def get_sentiment_vader(self, narrative_units:narrative_units.NarrativeUnits) -> narrative_units.NarrativeUnits:
        """
        add sentiment polarity to each narrative unit
        :return:
        """
        analyzer = SentimentIntensityAnalyzer()
        polarities = dict()
        for i in range(len(narrative_units)):
            text = narrative_units.get_text(i)
            polarity = analyzer.polarity_scores(text)
            narrative_units.add_property(i, "polarity", polarity)
        return narrative_units
    
    def get_sentiment_hugface(self,
                              narrative_units:narrative_units.NarrativeUnits,
                              model_name: str="siebert/sentiment-roberta-large-english",
                              max_length=1024
                              ) -> Tuple[narrative_units.NarrativeUnits, Dict[int, str]]:
        """
        add sentiment polarity to each narrative unit
        :return: narrative_units, id2label
        """

        self.sa_tokenizer = AutoTokenizer.from_pretrained(model_name, max_length=max_length)
        self.sa_model = AutoModelForSequenceClassification.from_pretrained(model_name, max_length=max_length)        
        print(f"max pos embeds: {self.sa_model.config.max_position_embeddings}")
        # self.sa_model.config.max_position_embeddings = max_length
        self.sa_model.eval()
        device = "cpu"
        if torch.cuda.is_available():
            device="cuda"
            self.sa_model.to(device)
        print(f"Is model on GPU?: {next(self.sa_model.parameters()).is_cuda}")


        for i in range(len(narrative_units)):
            text = narrative_units.get_text(i)
            input_ids = self.sa_tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length).input_ids
            input_ids = input_ids.to(device)
            output = self.sa_model(input_ids)
            # delete gradient and move to cpu
            # also turn it into numpy array
            polarity = output.logits.cpu().squeeze().detach().numpy()
            narrative_units.add_property(i, "polarity", polarity)
        return narrative_units, self.sa_model.config.id2label

    @PendingDeprecationWarning
    def get_conversations(self, nlp, doc):
        # detect conversations and its indexes
        tracker = self.find_conversations(nlp, doc)

        # find the speaker and addressee of each conversation
        for i, val in tracker.items():
            # get the speaker and addressee
            speaker, addressee = self.identify_sp_ad_sent(doc, val)
            tracker[i]["speaker"] = speaker
            tracker[i]["addressee"] = addressee

    @PendingDeprecationWarning
    def find_conversations(self,
                             nlp: spacy.language.Language,
                             doc: spacy.tokens.doc.Doc,
                             ) -> dict[dict[str: str]: int]:
        """
        Detect every conversation in the narrative units
        :param nlp: spacy language object
        :param doc: spacy.tokens.doc.Doc object
        :return:
        """
        # reference:
        # https://op.europa.eu/en/web/eu-vocabularies/formex/physical-specifications/character-encoding/quotation-marks
        # spacy does not tokenize and single out an apostrophe and Matcher is a token-based algorithm
        # So we do not consider a case where the matcher picks an apostrophe used for a contraction

        quo_start = ["\u0022", "\u0027", "\u0060", "\u00AB", "\u2018", "\u201C", "\u2039"]
        quo_end = ["\u0022", "\u0027", "\u00B4", "\u00BB", "\u2019", "\u201D", "\u203A"]
        pattern = r''
        for start, end in zip(quo_start, quo_end):
            pattern += f"{start}.*?{end}|"
        pattern = rf"({pattern})"

        # すべてのマッチを見つける
        re_matches = re.findall(pattern, doc.text)
        num = 0
        tracker = {}
        for match in re_matches:
            if match == "":
                continue
            tracker[num] = dict()
            tracker[num]["quote"] = match

        done = []
        for sent in list(doc.sents):
            for i, match in tracker.items():
                if i in done:
                    continue
                match = match["quote"]
                if match not in sent.text:
                    continue
                quote_start, quote_end = None, None
                for token in sent:
                    if token.text == match[0] and quote_start is None:
                        quote_start = token.i
                    elif token.text == match[-1]:
                        quote_end = token.i
                tracker[i]["sent"] = sent
                tracker[i]["sent start"] = sent.start
                tracker[i]["sent end"] = sent.end
                tracker[i]["quote start"] = quote_start
                tracker[i]["quote end"] = quote_end
                done.append(i)
            if len(done) == len(tracker):
                break
        return tracker
    
    @PendingDeprecationWarning
    def identify_sp_ad_sent(self, doc, tracker: dict[str]) -> dict[str: dict[str, int]]:
        """
        Identify the speaker and addressee of a conversation
        :param doc: spacy.tokens.doc.Doc object
        :param tracker: an instance of the tracker dictionary
        :return: dictionary of speaker and addressee as a spacy token object
        """
        # get the speaker and addressee
        speaker = []
        addressee = []
        in_quote = False
        # get the speaker and addressee
        for token in doc[tracker["sent start"]:tracker["sent end"]]:
            if token.is_quote:
                in_quote = not in_quote
            if token.dep_ == "nsubj" and in_quote is False:
                speaker.append(token)
            elif (token.dep_ == "dobj" or token.dep_ == "pobj") and in_quote is False:
                addressee.append(token)
        return {"speaker": speaker, "addressee": addressee}

    @PendingDeprecationWarning
    def identify_sp_ad_context(self, doc, tracker):
        sent = doc[tracker["sent start"]:tracker["sent end"]]
        para_id = sent[0]._.paragraph_id
        para = doc._.paragraphs[para_id]

        # identify addressee when it's missing
        if tracker["addressee"] is None:
            for token in para:
                if token.dep_ == "nsubj" and token.head == tracker["speaker"]:
                    tracker["addressee"].append(token)




"""
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
"""