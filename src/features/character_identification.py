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

# import local files
from src.data import make_dataset


class CharacterIdentification:
    def __init__(self, text):
        # set format: (name, gender)
        self.chars = None
        self.nlp = spacy.load("en_core_web_trf")
        self.doc = self.nlp(text)

    def detect_characters(self):
        """
        (1) use Named Entitiy Recognition (NER) to identify person entities
        """

        chars = defaultdict(
            lambda: ["GENDER", []]
        )
        for i, ent in enumerate(self.doc.ents):
            if ent.label_ == "PERSON":
                # in the set, we have {name: (gender, [**index])}
                # ent is spacy.tokens.span.Span and has start attribute (index of the span in the doc)
                chars[ent.text][1].append(ent.start)
        self.chars = chars
        return chars

    def annotate_gender(self):
        """
        (2) automatically anotate a gender to each entity based on:
            (a) lists of male first names and female first names
            (b) titles such as Mr., Mrs., or Lord etc...
            (c) detecting pronouns such as him, her, his, her, himself, and herself etc...

        gender options: MALE, FEMALE, UNKNOWN
        """

        gender_undefined = [name for name in self.chars.keys()]

        # identification by titles
        female_titles = ["mrs.", "mrs", "miss.", "miss", "mis.", "mis"]
        male_titles = ["mr.", "mr"]
        title_name = self._match_gender_title()
        for title, name in title_name:
            if name.text not in self.chars.keys():
                continue
            if title.text.lower() in female_titles:
                self.chars[name.text][0] = "FEMALE"
            elif title.text.lower() in male_titles:
                self.chars[name.text][0] = "MALE"
            gender_undefined.remove(name.text)
        # return complete character dict if gender undefined is finished
        if len(gender_undefined) == 0:
            return self.chars

        # identificaiton by name
        male_names, female_names = make_dataset.get_namelists()
        temp = gender_undefined.copy()
        for name in temp:
            print(name)
            if name in male_names:
                self.chars[name][0] = "MALE"
                gender_undefined.remove(name)
            elif name in female_names:
                self.chars[name][0] = "FEMALE"
                gender_undefined.remove(name)
            else:
                pass
        # return complete character dict if gender undefined is finished
        if len(gender_undefined) == 0:
            return self.chars

        # identification by pronouns
        # for name in gender_undefined:
        #     spans = self.chars[name][2]


    def _match_gender_title(self):
        # (1) honorific matcher

        # use REGEX experession
        #   [ri] means a token has either r or s after M
        #   s{0,2} means the s can appear 0 through 2 times
        #   .? means the period can appear 0 or 1 time
        # with the REGEX expression, we can cover Mr., Mrs., Miss., and Mis., with/without a following period
        pattern = [
            {"TEXT": {"REGEX": "M[ri]s{0,2}\.?"}},
            {"POS": "PROPN", "OP": "+"}
        ]

        matcher = Matcher(self.nlp.vocab)
        matcher.add("TITLE", [pattern])
        matches = matcher(self.doc)
        title_name = set()
        for match in matches:
            title_name.add((self.doc[match[1]], self.doc[match[1]+1:match[2]]))
        return title_name

    def _find_pronoun(self, token_idxes):
        mentions = []
        i = 0
        j = 0
        sents_num = 0
        while True:
            token_idx = token_idxes[i]
            sent = list(self.doc.sents)[j]
            sents_num += len(list(sent))
