
# import libraries
from collections import defaultdict
import spacy
from spacy.matcher import Matcher
from copy import deepcopy

# import local files
from src.data import make_dataset

class GenderAnnotation:
    def __init__(self, nlp, doc, chars:defaultdict):
        """
        """

        self.nlp = nlp
        self.doc = doc
        self.chars = chars

    def annotate_gender_by_titles_simple(self):
        female_titles, male_titles, _ = make_dataset.get_titles()
        name_genders = {
            name: "UNKNOWN" for name in list(self.chars.keys())
        }

        for name, character_obj in self.chars.items():
            title:str = character_obj.name_parsed.title
            # remove a period
            title = title.replace(".", "")

            if title == '':
                continue
            else:
                if title in female_titles:
                    name_genders[name] = "FEMALE"
                elif title in male_titles:
                    name_genders[name] = "MALE"
                else:
                    name_genders[name] = "UNKNOWN"
        return name_genders

    @DeprecationWarning
    def annotate_gender_by_titles(self):
        """
        This method is deprecated if character names are extracted with titles
        :return:
        """
        # identification by titles
        female_titles, male_titles, _ = make_dataset.get_titles()

        name_genders = {}
        for name in list(self.chars.keys()):
            name_genders[name] = []

        title_name = self._match_gender_title(male_titles, female_titles)
        for title, name in title_name:
            title = title.text
            # if the name is not in the default dict, skip the process
            if name.text not in self.chars.keys():
                continue

            # remove .
            if "." in title:
                title = title.replace(".", "")
            if title in female_titles:
                name_genders[name.text].append("FEMALE")
            elif title in male_titles:
                name_genders[name.text].append("MALE")
        # re-assign the most frequent gender to each person
        for name, gender in name_genders.items():
            size = len(gender)

            if size == 0:
                name_genders[name] = "UNKNOWN"
            elif gender.count("FEMALE") >= size/2:
                name_genders[name] = "FEMALE"
            elif gender.count("MALE") >= size/2:
                name_genders[name] = "MALE"
        return name_genders

    def _match_gender_title(self, male_titles, female_titles):
        # (1) honorific matcher

        # use REGEX experession
        #   [ri] means a token has either r or s after M
        #   s{0,2} means the s can appear 0 through 2 times
        #   .? means the period can appear 0 or 1 time
        # with the REGEX expression, we can cover Mr., Mrs., Miss., and Mis., with/without a following period
        titles = male_titles.union(female_titles)
        normal_expression = ""
        for title in titles:
            normal_expression += f"{title}\.?|"
        normal_expression = f"({normal_expression[:-1]})"
        # "(M[ri]s{0,2}\.? | sir\. | sord\. | lady\.)"

        pattern = [
            {"TEXT": {"REGEX": normal_expression}},
            {"POS": "PROPN", "OP": "+"}
        ]

        matcher = Matcher(self.nlp.vocab)
        matcher.add("TITLE", [pattern], greedy="LONGEST")
        matches = matcher(self.doc)
        title_name = list()
        for match in matches:
            title_name.append((self.doc[match[1]], self.doc[match[1]+1:match[2]]))
        return title_name

    def annotate_gender_by_names(self):
        # identificaiton by name
        female_names, male_names = make_dataset.get_namelists()
        names = list(self.chars.keys()).copy()
        name_genders = {}

        for name in list(names):
            first = self.chars[name].name_parsed.first
            if first in male_names:
                name_genders[name] = "MALE"
            elif first in female_names:
                name_genders[name] = "FEMALE"
            else:
                # this condition includes a case where first is None
                name_genders[name] = "UNKNOWN"
        return name_genders

    def annotate_gender_by_pronouns(self):
        names = list(self.chars.keys())
        name_genders = {}
        # identification by pronouns
        for name in names:
            # get a list of indexes of a propernoun appearing in the doc
            spans = self.chars[name].occurences
            # get a list of pronouns appearing in the sentences that each propernoun is in
            pronouns = self._find_pronouns(spans)
            # assign the most likely gender to the character from the list of pronouns
            gender = self._assign_gender_by_pronouns(pronouns)
            name_genders[name] = gender
        return name_genders

    def _find_pronouns(self, token_idxes):
        mentions = []
        i = 0
        j = 0
        start = 0
        end = 0
        while j < len(list(self.doc.sents))-1:

            # print(f"j: {j}")
            # print(f"i: {i}")

            # i is for indexing a token
            # j is for indexing a sentence
            # start is the number of tokens until the beginning of each sentence
            # end is the number of tlekns until the end of each sentence
            token_idx = token_idxes[i]

            # print(token_idx)

            # if the sentence is not the first one, add the length of previous sentence to start
            if j > 0:
                start += len(list(list(self.doc.sents)[j-1]))
            sent = list(self.doc.sents)[j]
            end += len(list(sent))

            # print(sent)
            # print(f"start: {start}")
            # print(f"end: {end}")

            # continue to scan through teh sentence if the token index is inside sentence
            # purposefully, also extract the pronouns even if a new token index appears in the sentence,
            # assuming that concurrent appearences strongly indicate the gender tallying the pronouns
            while start <= token_idx < end and i < len(token_idxes)-1:
                pronouns = self._match_pronouns(sent)
                mentions += pronouns
                i += 1
                token_idx = token_idxes[i]

                # print(pronouns)
                # print("\t =====================================================================")
            j += 1
            # print("------------------------------------------------")
        return mentions

    def _match_pronouns(self, sent):
        """
        find pronouns from a sentence
        :param sent: Spacy Sentence
        :return: a list of pronouns in SpaCy token
        """
        male_pattern = [
            {"LOWER": {"IN": ["he", "his", "him", "himself"]}}
        ]
        female_pattern = [
            {"LOWER": {"IN": ["she", "her", "hers", "herself"]}}
        ]

        matcher = Matcher(self.nlp.vocab)
        matcher.add("PRONOUN", [male_pattern, female_pattern])
        matches = matcher(sent)

        pronouns = []
        for match in matches:
            # print(f"match: {match}")
            pronouns.append(sent[match[1]:match[2]])
        return pronouns

    def _assign_gender_by_pronouns(self, pronouns, threshold = 0.8):
        """
        This method takes a list of pronouns and determines the gender based on the most appearing gender categories
        :param pronouns: list
        :return: the most likely gender
        """
        male, female = 0, 0
        size = len(pronouns)
        male_pronouns = ["he", "his", "him", "himself"]
        female_pronouns = ["she", "her", "hers", "herself"]
        for pron in pronouns:
            if pron.text.lower() in male_pronouns:
                male += 1
            elif pron.text.lower() in female_pronouns:
                female += 1

        gender = 'UNKNOWN'
        if male > female:
            # if the male pronouns are more than the percentile of the threshold of the whole list
            if male/size >= threshold:
                gender = "MALE"
        elif female > male:
            # if the female pronouns are more than the percentile of the threshold of the whole list
            if female/size >= threshold:
                gender = "FEMALE"
        return gender
