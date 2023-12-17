"""
This .py file is a set of functions that help identify characters in a text

Steps:
(1) use Named Entitiy Recognition (NER) to identify person entities
(2) automatically anotate a gender to each entity based on:
    (a) honorific or titles such as Mr., Mrs., or Lord etc...
    (b) lists of male first names and female first names
    (c) detecting pronouns such as him, her, his, her, himself, and herself etc...
(3) integrate person entities that refer to the same characters by:
    (a) grouping person names with similar names (refer to
    https://aclanthology.org/W14-0905/ for more information)
    (b) by excluding pairs that satisfy the following criteria:
        "(1) the inferred genders of both names differ
        (2) both names share a common surname but different first names
        (3) the honorific of both names differ, e.g., “Miss” and “Mrs.”"
        (reference: https://aclanthology.org/D15-1088/)
"""

# import libraries
import spacy
from spacy.matcher import Matcher
from collections import defaultdict
from nameparser import HumanName

# import local files
from src.data import make_dataset
from src.features.char_id._gender_annotation import GenderAnnotation


class CharacterIdentification(GenderAnnotation):

    def __init__(self, text):
        # set format: {name: [GENDER, [TOKEN INDEXES]]}
        self.chars = None
        self.nlp = spacy.load("en_core_web_trf")
        self.doc = self.nlp(text)

    def detect_characters(self):
        """
        (1) use Named Entitiy Recognition (NER) to identify person entities
        """

        chars = defaultdict(
            lambda: ["GENDER UNDEFINED", [], "FIRST NAME", "LAST NAME"]
        )
        for i, ent in enumerate(self.doc.ents):
            if ent.label_ == "PERSON":
                # in the set, we have {name: (gender, [**index])}
                # ent is spacy.tokens.span.Span and has start attribute (index of the span in the doc)

                # print(f"ent.text: {ent.text}")
                # print(f"ent.label_: {ent.label_}")
                # print(f"ent.start: {ent.start}")
                # print(f"self.doc[ent.start-10:ent.start+10]: {self.doc[ent.start]}")
                # print("===============================================")
                name = ent.text
                name_parsed = HumanName(name)
                chars[name][1].append(ent.start)
                chars[name][2] = name_parsed.first
                chars[name][3] = name_parsed.last
        self.chars = chars
        return chars

    def annotate_gender(self):
        """
        (2) automatically anotate a gender to each entity based on:
            (a) lists of male first names and female first names
            (b) titles such as Mr., Mrs., or Lord etc...
            (c) detecting pronouns such as him, her, his, her, himself, and herself etc...
            "a counter keeps track of counts of ‘his’ and ‘himself’ (on the one hand), and of ‘her’ and ‘herself’
            (on the other) appearing in a win- dow of at most 3 words to the right of the name."
            https://aclanthology.org/W14-0905/
        gender options: MALE, FEMALE, UNKNOWN
        """

        """a counter keeps track of counts of ‘his’ and ‘himself’ (on the one hand), and of ‘her’ and ‘herself’
            (on the other) appearing in a win- dow of at most 3 words to the right of the name."""

        if self.chars is None:
            raise ValueError(f"self.chars has not defined yet. Run detect_characters first.")
        # initialize the GenderAnnotation class upon defining self.char
        super().__init__(self.nlp, self.doc, self.chars)

        name_genders_title = self._annotate_gender_by_titiles()
        name_genders_name = self._annotate_gender_by_names()
        name_genders_pronoun = self._annotate_gender_by_pronouns()
        for name in list(self.chars.keys()):
            gender_t = name_genders_title[name]
            gender_n = name_genders_name[name]
            gender_p = name_genders_pronoun[name]

            genders = [gender_t, gender_n]
            size = len(genders)
            size -= genders.count("UNKNOWN")

            # the pronoun approach is quite unstable
            # use the pronoun approach only if the first two gender approaches cannot identify a gender

            # if all the specified genders in the list are FEMALE
            if genders.count("FEMALE") == size:
                self.chars[name][0] = "FEMALE"
            # if all the specified genders in the list are MALE
            elif genders.count("MALE") == size:
                self.chars[name][0] = "MALE"
            # if the two of the elements are FEMALE and MALE or all undefined
            else:
                self.chars[name][0] = gender_p
        return self.chars
