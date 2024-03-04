from nameparser import HumanName
from src.tools.data_based_name_parser import NameParserChecker

class Character:
    def __init__(self, name:str):
        self.name = name
        self.name_parsed = NameParserChecker(name)
        self.gender = "GENDER UNDEFINED"
        self.occurences = []
        self.id = None

        # self.possible_referents = self.getPossibleRerefents()

    def update_gender(self, gender):
        self.gender = gender

    def append_occurences(self, start_idx:int):
        self.occurences.append(start_idx)

    def __str__(self):
        print(self.name)

    def info(self):
        inf = {
            'name': self.name,
            'name_parsed': self.name_parsed,
            'gender': self.gender,
            'occurences': self.occurences,
            'referent': self.referent
        }
        return inf

    def update_referent(self, referent):
        self.referent = referent
