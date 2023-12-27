# import libraries

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

    def __init__(self, chars):
        self.chars = chars
        self.hypocorisms = make_dataset.get_hypocorisms(nicknames_for_names=True)

        # a dict for storing possible referents of each name
        self.char_referents = {
            name: [] for name in list(self.chars)
        }

    def unify_characters(self):
        pass

    def unify_by_hypocorisms(self):
        # for each character
        referents = self.char_referents.copy()
        for character in list(self.chars.values()):
            # get the first name
            first = character.name_parsed.first
            # if the character doesn't have a first name, then skip it
            if first is None:
                continue
            initial = first.upper()[0]
            # if the name is in the initial's index of the hypocorisms dictionary
            if first in self.hypocorisms[initial]:
                # add the list of referents to the self.char_referents list
                self.char_referents[character.name].extend(self.hypocorisms[initial][first])
            else:
                # if not, the first name refers to the person him/herself
                self.char_referents[character.name].append("SELF")
        return self.char_referents

    def unify_by_similarity(self):
        pass

