# import libraries

# import local files
from src.data import make_dataset

# References:


class UnifyOccurences:
    """
    This class tries to unify different referents to the same character.
    At the end of the main unify_occurences method, the class returns
    a dictionary of names and corresponding Character classes with a referent information
    A root referent should be that of the longest string lenth.
    e.g. Mr. Holmes, Holmes, and Sherlock should all refer to Mr. Sherlock Holmes
    """
    def __init__(self, chars):
        self.chars = chars
        self.hypocorisms = make_dataset.format_hypocorisms()

        # a dict for storing possible referents of each name
        self.char_referents = {
            name: [] for name in list(self.chars)
        }

    def unify_by_hypocorisms(self):
        # for each character
        for character in list(self.chars.values()):
            # get the capitalized initial of his/her first name
            initial = character.name_parsed.first.upper()[0]
            # if the name is in the initial's index of the hypocorisms dictionary
            if character.name in self.hypocorisms[initial]:


