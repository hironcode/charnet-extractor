from nameparser import HumanName

class Character:
    def __init__(self, name:str):
        self.name = name
        self.name_parsed = HumanName(name).as_dict()
        self.gender = "GENDER UNDEFINED"
        self.occurences = []
        self.referent = "REFERENT UNDEFINED"

    def updateGender(self, gender):
        self.gender = gender

    def appendOccurences(self, start_idx:int):
        self.occurences.append(start_idx)

    def __str__(self):
        print(self.name)

    def updateReferent(self, referent):
        self.referent = referent

