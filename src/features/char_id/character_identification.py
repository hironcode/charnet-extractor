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
from src.features.char_id._gender_annotation import GenderAnnotation
from src.features.char_id._unify_occurences import OccurenceUnification
from src.tools.character_entity import Character
from src.models import model_saver


class CharacterIdentification:
    def __init__(self, text, title):
        # set format: {name: Character Class}
        self.title = title
        self.chars = None
        model = "en_core_web_trf"
        self.nlp = spacy.load(model)

        # load doc object
        model_path = model_saver.get_spacy_doc_path(title, doc_type=model.replace("en_core_web_", ""))
        if model_saver.exists(model_path):
            self.doc = model_saver.get_model(model_path)
            print('exist!')
        else:
            self.doc = self.nlp(text)
            model_saver.save_model(model_path, self.doc)

    def detect_characters(self):
        """
        (1) use Named Entitiy Recognition (NER) to identify person entities
        """

        chars = {}
        female_titles, male_titles = make_dataset.get_titles()
        titles = female_titles.union(male_titles)
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

                # identify a title if the name has one
                if ent.start - 1 >= 0:
                    title = self.doc[ent.start - 1].text
                    title_w_o_period = title.replace(".", "")
                else:
                    title = None
                    title_w_o_period = None

                if title_w_o_period in titles:
                    name = f"{title} {name}"

                # create a dictionary index if the name does not exist in the dict yet
                # the name might have a title
                if name not in chars.keys():
                    character = Character(name)
                    chars[name] = character
                chars[name].append_occurences(ent.start)
        self.chars = chars
        return chars

    def title(self):
        pass

    def annotate_gender(self):
        """
        (2) automatically anotate a gender to each entity based on:
            (a) lists of male first names and female first names
            (b) titles such as Mr., Mrs., or Lord etc...
            (c) detecting pronouns such as him, her, his, her, himself, and herself etc...
            "a counter keeps track of counts of ‘his’ and ‘himself’ (on the one hand), and of ‘her’ and ‘herself’
            (on the other) appearing in a window of at most 3 words to the right of the name."
            https://aclanthology.org/W14-0905/
        gender options: MALE, FEMALE, UNKNOWN
        """

        """a counter keeps track of counts of ‘his’ and ‘himself’ (on the one hand), and of ‘her’ and ‘herself’
            (on the other) appearing in a win- dow of at most 3 words to the right of the name."""

        if self.chars is None:
            raise ValueError(f"self.chars has not defined yet. Run detect_characters first.")
        # initialize the GenderAnnotation class upon defining self.char
        # super().__init__(self.nlp, self.doc, self.chars)
        ga = GenderAnnotation(self.nlp, self.doc, self.chars)

        name_genders_title = ga.annotate_gender_by_titles_simple()
        print(f"_annotate_gender_by_titles_siple: "
              f"{name_genders_title}")

        name_genders_name = ga.annotate_gender_by_names()
        print(f"_annotate_gender_by_names:"
              f"{name_genders_name}")

        name_genders_pronoun = ga.annotate_gender_by_pronouns()
        print(f"_annotate_gender_by_pronouns:"
              f"{name_genders_pronoun}")

        for name in list(self.chars.keys()):
            gender_t = name_genders_title[name]
            gender_n = name_genders_name[name]
            gender_p = name_genders_pronoun[name]

            genders = [gender_t, gender_n]
            size = len(genders)
            size -= genders.count("UNKNOWN")

            # the pronoun approach is quite unstable
            # use the pronoun approach only if the first two gender approaches cannot identify a gender

            # if all the genders in the list are UNKNOWN
            if size == 0:
                self.chars[name].update_gender(gender_p)

            # if all the specified genders in the list are FEMALE
            if genders.count("FEMALE") == size:
                self.chars[name].update_gender("FEMALE")
            # if all the specified genders in the list are MALE
            elif genders.count("MALE") == size:
                self.chars[name].update_gender("MALE")
            # if the two of the elements are FEMALE and MALE or all undefined
            else:
                self.chars[name].update_gender(gender_p)
        return self.chars

    def unify_occurences(self) -> [tuple]:
        """
        Rules (https://aclanthology.org/D15-1088/)
        Two vertices cannot be merged if
        (1) the inferred genders of both names differ,
        (2) both names share a common surname but different first names, or
        (3) the honorific of both names differ, e.g., “Miss” and “Mrs.”
        :return: list representation of networkX nodes/edges
        """
        if self.chars is None:
            raise ValueError(f"self.chars has not defined yet. Run detect_characters first.")
        ou = OccurenceUnification(self.chars)
        referents = ou.unify_referents()

        # merge occurences
        same_chars = {}
        # check through if each referent exists in the story (or self.chars)
        chars_all = set(self.chars.keys())

        """possible to make this part faster"""

        # for each character name
        for name, ref in referents.items():
            # fetch possible referents in a form of set
            chars_potential = set(ref)
            # get the character names that exists in the story (or self.chars) out of the potential character names
            chars_present = chars_all.intersection(chars_potential)
            same_chars[name] = chars_present

        char_groups = []
        # i for list elements in the first dimension
        # j for str elements (names) in the second dimension
        i = 0
        # skip
        skip_list = []

        # get a list of tuples of names and referents in a decending order based on the length of names
        names_refs = sorted(list(same_chars.items()), key=lambda x: len(x[0]), reverse=True)
        while i < len(same_chars):
            name = names_refs[i][0]
            if name in skip_list:
                i += 1
                continue
            refs: set = names_refs[i][1]
            for ref in refs:
                skip_list.append(ref)
                if ref == name:
                    continue
                refs2: set = same_chars[ref]
                refs = refs.union(refs2)
            char_groups.append(list(refs))
            i += 1
        return char_groups
