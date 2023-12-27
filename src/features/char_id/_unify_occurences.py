# import libraries
import src.tools.character_entity
# import local files
from src.data import make_dataset

"""
Approach
(*) Unify characters by making possible shorter names of a longer name
    (
    https://aclanthology.org/D15-1088/,
    https://aclanthology.org/W14-0905/,
    https://aclanthology.org/P10-1015/,
    )
(*) Unify characters by gender
(*) Unify characters by hypocorisms
    (
    https://aclanthology.org/D15-1088/,
)

Rules (https://aclanthology.org/D15-1088/)
Two vertices cannot be merged if
(1) the inferred genders of both names differ,
(2) both names share a common surname but different first names, or
(3) the honorific of both names differ, e.g., “Miss” and “Mrs.”
"""


class OccurenceUnification:
    """
    This class tries to unify different referents to the same character.
    At the end of the main unify_occurences method, the class returns
    a dictionary of names and corresponding Character classes with a referent information
    A root referent should be that of the longest string lenth.
    e.g. Mr. Holmes, Holmes, and Sherlock should all refer to Mr. Sherlock Holmes
    """

    def __init__(self, chars:dict):
        self.chars = chars
        self.hypocorisms = make_dataset.get_hypocorisms(nicknames_for_names=False)

        # a dict for storing possible referents of each name
        self.char_referents = {
            name: [] for name in list(self.chars)
        }

    def unify_characters(self):
        pass

    def unify_by_hypocorisms(self):
        # for each character
        for name, character in self.chars.items():
            # get the first name
            first = character.name_parsed.first
            # if the character doesn't have a first name, then skip it
            if first == '':
                continue
            initial = first.upper()[0]
            # if the name is in the initial's index of the hypocorisms dictionary
            if first in self.hypocorisms[initial]:
                # add the list of referents to the self.char_referents list
                self.char_referents[name].extend(self.hypocorisms[initial][first])
            else:
                # if not, the first name refers to the person him/herself
                self.char_referents[character.name].append("SELF")
        return self.char_referents

    def unify_by_similarity(self):
        """
        reference: https://aclanthology.org/W14-0905/
        Matching algorithm.
        A matching algorithm is responsible for grouping the different coreferents
        of the same entity from less to more ambiguous:
        1. Names with title, first name and last name (e.g. ‘Miss Elizabeth Bennet’).
        2. Names with first name and last name (e.g. ‘Elizabeth Bennet’).
        3. Names with title and first name (e.g. ‘Miss Elizabeth’).
        4. Names with title and last name (e.g. ‘Miss Bennet’).
        5. Names with only first name or last name (e.g. ‘Elizabeth’ or ‘Bennet’).
        :return:
        """

    def get_possible_referent(self, character:src.tools.character_entity.Character):
        """
        reference: https://aclanthology.org/W14-0905/
        """

        title = character.name_parsed.title
        first = character.name_parsed.first
        last = character.name_parsed.last
        middle = character.name_parsed.middle

        possible = {
            "title first last": '',
            "title first_ini last": '',
            # nickname might take multiple forms so list
            "title nickname last": [],
            "title last"
            "first_ini last": '',
            "first last": '',
            "title first": '',
            "title last": '',
            "first": '',
            "last": '',

            # with middle names
            "title first middle last": '',
            "title first_ini middle last": '',
            "title nickname middle last": [],
            "first middle": '',
            "title first middle": '',
            "first middle last": '',
            "nickname last": [],
        }

        # create possible referents only if the name has at least first name and last name
        if first == '' or last == '':
            return possible

        initial = first.upper()[0]

        # if the name has a title
        if title != '':
            possible["title first last"] = f"{title} {first} {last}"
            # add a period after an initial
            possible["title first_ini last"] = f"{title} {initial}. {last}"
            for nickname in self.hypocorisms[initial][first]:
                possible["title nickname last"].append(f"{title} {nickname} {last}")
                # if the name contians a middle name
                if middle != '':
                    possible["title nickname middle last"] = f"{title} {nickname} {middle} {last}"

            possible["title first"] = f"{title} {first}"
            possible["title last"] = f"{title} {last}"

        if middle != '':
            possible['first middle'] = f"{first} {middle}"
            possible["first middle last"] = f"{first} {middle} {last}"

        if middle != '' and title != '':
            possible["title first middle last"] = f"{title} {first} {middle} {last}"
            possible["title first_ini middle last"] = f"{title} {initial} {middle} {last}"
            possible["title first middle"] = f"{title} {first} {middle}"

        possible["first last"] = f"{first} {last}"
        possible["first"] = first
        possible["last"] = last
        for nickname in self.hypocorisms[initial][first]:
            possible['nickname last'].append(f"{nickname} {last}")

        return possible


