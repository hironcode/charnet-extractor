from collections import defaultdict
from spacy.tokens import Doc
from src.tools.character import Character, AllCharacters
import math
from typing import Any, Dict

class NarrativeUnits:
    def __init__(
            self,
            title:str,
            docs:dict[int: Doc],
            chars: AllCharacters,
            unit_percentile:float=0.025,
            ) -> None:
        """
        Creates a dictionary-based class for narrative units

        :param docs: dictionary of Doc objects. Sometimes a text goes over the Doc size limit.
        :param title: title of the story
        :param unit_percentile: the percentage of the total number of sentences that each narrative unit should have
        """


        self.units = defaultdict(dict)
        self.docs = docs
        self.title = title
        self.chars = chars
        self.unit_percentile = unit_percentile


        # Push chars in ascending order based on their token index
        idxs = [(idx, char) for char in chars.get_all_characters() for idx in char.occurences]
        idxs = sorted(idxs, key=lambda x: x[0], reverse=False)



        # calculate the total number of tokens in the text
        all_sent_num = 0
        for doc in docs.values():
            all_sent_num += len(list(doc.sents))
        # calculate the number of sentences for each narrative unit
        each_unit_sent_num = math.ceil(all_sent_num * unit_percentile)

        # index of each narrative unit
        unit_idx = 0
        # separate token index is necessary to keep track of the number of tokens across different Doc objects
        sent_idx = 0
        # token index for character occurences
        token_idx = 0
        # string object that stores the actual text of each narrative unit
        narrative = ''
        pointer = 0

        print(f"len(idxs): {len(idxs)}")

        characters = []
        for doc in docs.values():
            doc: Doc
            for sent in doc.sents:
                sent_idx += 1
                token_idx += len(sent)
                narrative += sent.text + " "

                if sent_idx == each_unit_sent_num:
                    # add the narrative-unit text to the dictionary
                    self.update_text(unit_idx, narrative)

                    # check what characters are in the unit
                    done = False
                    while not done:
                        idx, char = idxs[pointer]
                        print(f"idx: {idx}, token_idx: {token_idx}")
                        print(f"char: {char.name}")
                        
                        if pointer == len(idxs) - 1:    # otherwise, pointer will be out of range
                            done = True
                        elif idx <= token_idx:
                            characters.append(char)
                            pointer += 1
                        elif idx > token_idx:
                            done = True
                    self.add_property(unit_idx, "characters", characters)
                    characters = []
                    narrative = ""
                    unit_idx += 1
                    sent_idx = 0
        # add the last remaining sentences to the dictionary
        self.update_text(unit_idx, narrative)
        characters = [char for idx, char in idxs[pointer:]]
        self.add_property(unit_idx, "characters", characters)


    def get_text(self, unit_idx:int) -> str:
        """
        Get the text of the narrative unit

        :param unit_idx: index of the narrative unit
        :return: text of the narrative unit
        """
        return self.units[unit_idx]["text"]
    
    def update_text(self, unit_idx:int, text:str) -> None:
        """
        Update the text of the narrative unit

        :param unit_idx: index of the narrative unit
        :param text: new text of the narrative unit
        """
        self.units[unit_idx]["text"] = text

    def add_property(self, unit_idx:int, key:str, value:Any) -> None:
        """
        Add a property to the narrative unit

        :param unit_idx: index of the narrative unit
        :param key: key of the property
        :param value: value of the property
        """
        self.units[unit_idx][key] = value

    def get_property(self, unit_idx:int, key:str) -> Any:
        """
        Get the property of the narrative unit

        :param unit_idx: index of the narrative unit
        :param key: key of the property
        :return: value of the property
        """
        return self.units[unit_idx][key]
    
    def info(self):
        """
        Print the information of the narrative units
        """
        prop_num = len(list(self.units[0].keys()))
        if any(len(v) != prop_num for v in self.units.values()):
            raise ValueError(f"Properties of each narrative unit are not consistent. Please check the properties of each narrative unit.")
        
        print(f"Title: {self.title}")
        print(f"Property keys: {list(self.units[0].keys())}")
        print(f"Number of narrative units: {len(self.units)}")

        for unit_idx, unit in self.units.items():
            print(f"Unit {unit_idx}: {unit['text'][:50]}...")
            for key, value in unit.items():
                if key != 'text':
                    print(f"{key}: {value}")
            print()

    def __len__(self):
        return len(self.units)
    
    def __getitem__(self, unit_idx:int) -> Dict[str, Any]:
        return self.units[unit_idx]
    
    def keys(self):
        return self.units.keys()
    
    def values(self):
        return self.units.values()
    
    def items(self):
        return self.units.items()
    
    