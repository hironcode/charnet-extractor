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
from unionfind import unionfind
from wasabi import msg
from typing import Tuple

# import local files
from src.data import make_dataset
from src.features.char_id._gender_annotation import GenderAnnotation
from src.features.char_id._occurrence_unification import OccurrenceUnification
from src.tools.character import Character, AllCharacters
from src.models import mbank
from src.tools.character_grouping import CharacterGrouping


class CharacterIdentification:
    def __init__(self, nlp, doc):
        # set format: {name: Character}
        self.chars = AllCharacters({})
        self.occurrences = None
        self.nlp = nlp
        self.doc = doc

    def run(self) -> Tuple[dict[str: Character], list[list]]:
        """
        :return: a dictionary of character names (keys) and Character classes (values) and a list of co-occurrences
        """
        self.chars = self.detect_characters(self.chars)
        msg.good("Character Detection is done\n")
        msg.good("="*50)

        self.chars = self.annotate_gender(self.chars)
        msg.good("Gender Annotation is done\n")
        msg.good("=" * 50)

        self.chars, self.occurrences = self.unify_occurrences(self.chars)
        msg.good("Occurrence Unification is done\n")
        msg.good("=" * 50)

        # self.chars = self.assign_id(self.chars, self.occurrences)
        # msg.good("ID Assignment is done\n")
        # msg.good("="*50)

        return self.chars, self.occurrences

    def detect_characters(self, chars:AllCharacters) -> AllCharacters:
        """
        (1) use Named Entitiy Recognition (NER) to identify person entities
        :return: a dictionary of character names (keys) and Character classes (values)
        """

        female_titles, male_titles, common_titles = make_dataset.get_titles()
        # merge all title sets with operator "|" (union)
        titles = female_titles | male_titles | common_titles
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

                title = None
                # identify a title if the name has one
                if ent.start - 1 >= 0:
                    title = self.doc[ent.start - 1].text

                if title.replace(".", "") in titles:
                    name = f"{title} {name}"

                # create a dictionary index if the name does not exist in the dict yet
                # the name might have a title
                if name not in chars.get_names():
                    character = Character(name)
                    chars.add_character(name, character)
                    chars.assign_ids()
                id = chars.name_to_id(name)
                chars.append_occurence(id, ent.start)
        return chars

    def annotate_gender(self, chars: AllCharacters) -> AllCharacters:
        """
        (2) automatically anotate a gender to each entity based on:\n
            (a) lists of male first names and female first names\n
            (b) titles such as Mr., Mrs., or Lord etc...\n
            (c) detecting pronouns such as him, her, his, her, himself, and herself etc...\n
            "a counter keeps track of counts of ‘his’ and ‘himself’ (on the one hand), and of ‘her’ and ‘herself’
            (on the other) appearing in a window of at most 3 words to the right of the name."\n
            https://aclanthology.org/W14-0905/\n
        gender options: MALE, FEMALE, UNKNOWN\n
        :return: a dictionary of character names (keys) and Character classes (values) with gender annotated
        """

        """a counter keeps track of counts of ‘his’ and ‘himself’ (on the one hand), and of ‘her’ and ‘herself’
            (on the other) appearing in a win- dow of at most 3 words to the right of the name."""

        if chars is None:
            raise ValueError(f"self.chars has not defined yet. Run detect_characters first.")
        # initialize the GenderAnnotation class upon defining self.char
        ga = GenderAnnotation(self.nlp, self.doc, chars.chars)

        name_genders_title = ga.annotate_gender_by_titles_simple()
        print(f"_annotate_gender_by_titles_simple: "
              f"{name_genders_title}")

        name_genders_name = ga.annotate_gender_by_names()
        print(f"_annotate_gender_by_names:"
              f"{name_genders_name}")
        
        # Dec/30/2024 - pronoun approach is quite unstable. We deprecate this for now.
        msg.warn("Dec/30/2024 - Pronoun approach is quite unstable. We deprecate this for now.")
        # name_genders_pronoun = ga.annotate_gender_by_pronouns()
        name_genders_pronoun = {name: "UNKNOWN" for name in chars.get_names()}
        print(f"_annotate_gender_by_pronouns:"
              f"{name_genders_pronoun}")

        for name in chars.get_names():
            gender_t = name_genders_title[name]
            gender_n = name_genders_name[name]
            gender_p = name_genders_pronoun[name]

            genders = [gender_t, gender_n]
            size = len(genders)
            size -= genders.count("UNKNOWN")

            # the pronoun approach is quite unstable
            # use the pronoun approach only if the first two gender approaches cannot identify a gender

            # if all the genders in the list are UNKNOWN
            id = chars.name_to_id(name)
            if size == 0:
                chars.update_gender(id, gender_p)
            # if all the specified genders in the list are FEMALE
            elif genders.count("FEMALE") == size:
                chars.update_gender(id, "FEMALE")
            # if all the specified genders in the list are MALE
            elif genders.count("MALE") == size:
                chars.update_gender(id, "MALE")
            # if the two of the elements are FEMALE and MALE or all undefined
            else:
                chars.update_gender(id, gender_p)
        print(f"_annotate_gender_final:",
              [char.name + ":" + char.gender for char in chars.get_all_characters()])
        return chars

    def _gender_matches(self, gender1, gender2):
        genders = [gender1, gender2]
        # if one of the two is unknown, count it as a gender match
        if genders.count("UNKNOWN") >= 1:
            return True
        # if two of them are the same
        elif genders.count("FEMALE") == 2 or genders.count("MALE") == 2:
            return True
        else:
            return False

    def unify_occurrences(self, chars:AllCharacters) -> list[list]:
        """
        Rules (https://aclanthology.org/D15-1088/)\n
        Two vertices cannot be merged if\n
        (1) the inferred genders of both names differ,\n
        (2) both names share a common surname but different first names, or\n
        (3) the title of both names differ, e.g., “Miss” and “Mrs.”\n
        :return: list representation of networkX nodes/edges
        """
        if chars is None:
            raise ValueError(f"chars has not defined yet. Run detect_characters first.")
        for char in chars.get_all_characters():
            if char.gender == "GENDER UNDEFINED":
                raise ValueError(f"annotate gender first by running annotate_gender method.")

        ou = OccurrenceUnification(chars.chars)
        referents = ou.unify_referents()

        # merge occurrences
        same_chars = {}
        # check through if each referent exists in the story (or self.chars)
        chars_all = set(chars.get_names())

        """possible to make this part faster"""
        # for each character name
        for name, ref in referents.items():
            # fetch possible referents in a form of set
            chars_potential = set(ref)
            # get the character names that exists in the story (or self.chars) out of the potential character names
            chars_present = chars_all.intersection(chars_potential)
            same_chars[name] = chars_present
        
        del referents

        # filter referents that do not meet gender or title consistency
        to_remove = []
        for name, refs in same_chars.items():
            id = chars.name_to_id(name)
            gender1 = chars.get_gender(id)
            for ref in refs:
                # if the characters' genders do not match, they are different characters
                # UNKNOWNは許容する
                ref_id = chars.name_to_id(ref)
                gender2 = chars.get_gender(ref_id)
                if not self._gender_matches(gender1, gender2):
                    to_remove.append((name, ref))

                # if both have a title, but they do not match, they are two separate characters
                title1: str = chars.get_character_from_name(name).name_parsed.title
                title2: str = chars.get_character_from_name(ref).name_parsed.title
                if (title1 != '' and title2 != '') and (title1 != title2):
                    to_remove.append((name, ref))
                # otherwise, they are the same character
        for name, ref in to_remove:
            same_chars[name].discard(ref)

        # if the same consistent referent exists in two separate characters' possible referent set,
        # prioritize the most frequent one (https://aclanthology.org/W14-0905/, https://aclanthology.org/E12-1065/)
        # {[REFERENT, REFERING NAME, COUNT]}
        # e.g.: if Sam -> Samuel (who appears 15 times in the text) and Sam -> Samwise (who appears 5 times), 
        # then Sam should denote Samuel
        repeated_referents = defaultdict(lambda: [])
        for name, refs in same_chars.items():
            for ref in refs:
                repeated_referents[ref].append(name)

        # delete unrepeated referents
        to_remove = []
        for ref, repeat in repeated_referents.items():
            if len(repeat) <= 1:
                to_remove.append(ref)
        for ref in to_remove:
            repeated_referents.pop(ref)

        # use union-find algorithm to cluster separate names to each group
        char_groups = CharacterGrouping(chars.get_names())
        for name, refs in same_chars.items():
            for ref in refs:
                # if a referent is repeated, skip it
                if ref in list(repeated_referents.keys()):
                    continue
                char_groups.unite(name, ref)

        # unite a consistent but repeated reference with the most frequent one
        for ref, names in repeated_referents.items():
            max_name = names[0]
            max_occurrence = 0
            # fetch referring names of each referent and get the char name of the maximum occurrences
            for name in names:
                occ = len(chars.chars[name].occurences)
                if occ > max_occurrence:
                    max_name = name
                    max_occurrence = occ
            char_groups.unite(ref, max_name)

        """
        In the code above, we merged referents based on possible nicknames or possible combination of name particles made from referents that at least have first and last name.
        The following code is similar to above, but necessary to identify if a referent denotes a different referent that includes a name element the former referent does not have.
        e.g.: Does Mr. Holmes refers to Sherlock Holmes or Mycroft Holmes?
        """

        # merge each pair of names if they share the same gender or their titles are consistent
        # assign a name that potentially refers to different characters to the most frequent name too
        # Mr. Holmes -> Sherlock Holmes or Mycroft Holmes -> assign Sherlock as more frequent than Mycroft
        charlist = chars.get_names()
        correspondence = defaultdict(list)

        for i, char1 in enumerate(charlist[:-1]):
            first1 = chars.get_character_from_name(char1).name_parsed.first
            last1 = chars.get_character_from_name(char1).name_parsed.last
            title1: str = chars.get_character_from_name(char1).name_parsed.title
            l1 = [first1, last1, title1]
            if l1.count('') >= 2:
                continue

            for char2 in charlist[i+1:]:
                first2 = chars.get_character_from_name(char2).name_parsed.first
                last2 = chars.get_character_from_name(char2).name_parsed.last
                title2: str = chars.get_character_from_name(char2).name_parsed.title
                l2 = [first2, last2, title2]
                if l2.count('') >= 2:
                    continue
                
                
                # if the characters' genders do not match, they are different characters
                if chars.get_gender(chars.name_to_id(char1)) != chars.get_gender(chars.name_to_id(char2)):
                    continue
                # if both have a title, but if the titles are different, they are two separate characters
                elif (title1 != '' and title2 != '') and (title1 != title2):
                    continue
                elif first1 == first2 or last1 == last2:
                    correspondence[char1].append(char2)
                    correspondence[char2].append(char1)

        # assign a referent that potentially refers to different characters to the most frequent name
        # Mr. Holmes -> Sherlock Holmes or Mycroft Holmes -> assign Mr. Holmes to Sherlock as more frequent than Mycroft
        # unite a consistent but repeated reference with the most frequent one
        for char1, char2s in correspondence.items():
            max_name = char2s[0]
            max_occurrence = 0
            # fetch refering names of each referent and get the char name of the maximum occurences
            for name in char2s:
                occ = len(chars.get_character_from_name(name).occurences)
                if occ > max_occurrence:
                    max_name = name
                    max_occurrence = occ
            char_groups.unite(char1, max_name)

        # reset the occurrence matrix as new characters were added to this AllCharacter instance
        chars.reset_occurences()
        # update the occurence matrix in ALl Characters
        for group in char_groups.groups():
            ids = [chars.name_to_id(name) for name in group]
            chars.update_occurences_from_list(ids)

        return self.chars, char_groups.groups()
