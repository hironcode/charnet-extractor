from nameparser import HumanName
from src.tools.data_based_name_parser import NameParserChecker
import numpy as np
from typing import Dict, Any, Tuple, List

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
        return self.name

    def info(self):
        inf = {
            'name': self.name,
            'name_parsed': self.name_parsed,
            'gender': self.gender,
            'occurences': self.occurences,
            'referent': self.referent,
            'id': self.id
        }
        return inf

    def update_referent(self, referent):
        self.referent = referent


class AllCharacters:
    def __init__(self, chars: dict[str: Character]):
        self.chars = chars
        self.id_chars = {char.id: char for char in chars.values()}
        self.occurences = np.zeros((len(chars), len(chars)), dtype=int) # one for same characters, zero for different characters
        for i in range(len(chars)):
            self.occurences[i, i] = 1

    def get_names(self) -> list[str]:
        """
        Get the names of all characters in string format
        """
        return list(self.chars.keys())
    
    def update_id_chars(self) -> None:
        """
        Update the internal id_chars dictionary
        """
        self.id_chars = {char.id: char for char in self.chars.values()}
        

    def assign_ids(self) -> None:
        """
        Assign an ID to each character. Rewrites the ID if the character is already in the list
        """

        # apply sorting to save a consistent order
        id = 0
        for name in sorted(list(self.chars.keys())):
            self.chars[name].id = id
            id += 1
        self.update_id_chars()
    
    def id_to_name(self, id:int) -> str:
        return self.id_chars[id].name
    
    def name_to_id(self, name:str) -> int:
        return self.chars[name].id
    
    def add_character(self, name:int, character: Character) -> None:
        self.chars[name] = character
    
    def append_occurence(self, id:int, start_idx:int) -> None:
        name = self.id_to_name(id)
        self.chars[name].append_occurences(start_idx)

    def update_gender(self, id:int, gender:str) -> None:
        assert gender in ["MALE", "FEMALE", "UNKNOWN"], gender
        name = self.id_to_name(id)
        self.chars[name].update_gender(gender)

    def update_occurences_from_list(self, same_chars:list[int]) -> None:
        """
        Update the occurences matrix with the same characters

        :param same_chars: list of IDs of the same characters
        """
        self.occurences[same_chars, same_chars] = 1

    def get_occurences(self) -> int:
        """
        Get the number of occurences between two characters

        :param name1: name of the first character
        :param name2: name of the second character
        :return: number of occurences between the two characters
        """
        return self.occurences
    
    def reset_occurences(self) -> None:
        self.occurences = np.zeros((len(self.chars), len(self.chars)), dtype=int)
        for i in range(len(self.chars)):
            self.occurences[i, i] = 1
    
    def is_same_character(self, id1:int, id2:int) -> bool:
        return self.occurences[id1, id2] == 1

    def get_character_from_name(self, name:str) -> Character:
        return self.chars[name]
    
    def get_character_from_id(self, id:int) -> Character:
        name = self.id_to_name(id)
        try:
            return self.chars[name]
        except KeyError:
            return None
    
    def get_all_characters(self) -> list[Character]:
        return list(self.chars.values())
    
    def get_gender(self, id:int) -> str:
        if type(id) != int:
            raise ValueError(f"ID must be an integer, not {type(id)}")
        name = self.id_to_name(id)
        return self.chars[name].gender


    
    