from nameparser import HumanName

class Character:
    def __init__(self, name:str):
        self.name = name
        self.name_parsed = HumanName(name)
        self.gender = "GENDER UNDEFINED"
        self.occurences = []
        self.referent = "REFERENT UNDEFINED"

        # self.possible_referents = self.getPossibleRerefents()

    def updateGender(self, gender):
        self.gender = gender

    def appendOccurences(self, start_idx:int):
        self.occurences.append(start_idx)

    def __str__(self):
        print(self.name)

    def info(self):
        inf = {
            'name': self.name,
            'gender': self.gender,
            'occurences': self.occurences,
            'referent': self.referent
        }
        return inf

    def updateReferent(self, referent):
        self.referent = referent

    def getPossibleRerefents(self):
        possible = set()

        if not self.name_parsed.first and not self.name_parsed.last:
            return

        possible.add(self.name_parsed.first, self.name_parsed.last)