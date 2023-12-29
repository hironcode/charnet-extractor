from src.data import make_dataset
from nameparser import HumanName as _HumanName


class NameParserChecker:
    """
    This class compensates nameparser's misidentifications of last name and first name
    by refering to a set of first names and last names
    """
    def __init__(self, name):
        self.name = name
        self._name_parsed = _HumanName(name).as_dict()
        first, f_pos = self.check_first(self._name_parsed)
        last, l_pos = self.check_last(self._name_parsed)

        # overwrite name_parsed with correct parts of the name
        if first:
            self.first = first
            self._name_parsed['first'] = first

            # delete an element if the element in the original position is the same as the first name
            # this is for deleting redundancy in a case where only either a first or last name is specified
            if f_pos and first == self._name_parsed[f_pos]:
                self._name_parsed[f_pos] = ''
        else:
            self.first = ''
            self._name_parsed['first'] = ''

        if last:
            self.last = last
            self._name_parsed['last'] = last
            # delete an element if the element in the original position is the same as the first name
            # this is for deleting redundancy in a case where only either a first or last name is specified
            # if the original position is overwritten in the first name phase,
            # this statement does not make any changes in the dictionary
            if l_pos and last == self._name_parsed[l_pos]:
                self._name_parsed[l_pos] = ''
        else:
            self.last = ''
            self._name_parsed['last'] = ''

        # create instances of corrected name components
        self.middle = self._name_parsed['middle']
        self.suffix = self._name_parsed['suffix']
        self.nickname = self._name_parsed['nickname']
        self.title = self._name_parsed['title']


    def check_first(self, name_parsed):
        """
        :param name_parsed: dictionary
        :return: correct first name and the position that the first name was classified into
        """

        female_names, male_names = make_dataset.get_namelists()
        hypocorisms = set(make_dataset.get_hypocorisms(nicknames_for_names=True).keys())
        first = name_parsed['first']
        if first in female_names or first in male_names or first in hypocorisms:
            # if the parsed name object has a correct first name or nickname (like Em), return the first name
            return first, None
        else:
            # if not, the first name seems to be incorrect
            components = [
                'title',
                'middle',
                'last',
                'suffix',
                'nickname',
            ]
            for c in components:
                part = name_parsed[c]
                if part in female_names or part in male_names or part in hypocorisms:
                    # if the parsed name object has a part that exists in firstname or nickname list,
                    # return the part as a correct first name
                    return part, c
            # if no such part, return None, denoting that the full name doesn't have a first name
            return None, None

    def check_last(self, name_parsed):
        """
            :param name_parsed: dictionary
            :return: correct last name and the position that the last name was classified into
        """
        surnames = make_dataset.get_surnames()
        last = name_parsed['last']
        if last in surnames:
            return last, None
        else:
            # if not, the first name seems to be incorrect
            components = [
                'title',
                'first',
                'middle',
                'suffix',
                'nickname',
            ]
            for c in components:
                part = name_parsed[c]
                if part in surnames:
                    # if the parsed name object has a part that exists in the surname list,
                    # return the part as a correct surname
                    return part, c
            # if no such part, return None, denoting that the full name doesn't have a last name
            return None, None

    def as_dict(self):
        return self._name_parsed

    def __str__(self):
        return str(self.name)


if __name__ == '__main__':
    # test the performance

    # this does not make any differences.
    name1 = "Mrs. Emily Anderson"
    char1_parsed = _HumanName(name1)
    char1_checked = NameParserChecker(name1)
    print(f"{name1}\n")
    print(char1_parsed.as_dict())
    print(char1_checked.as_dict())
    print("==================================")

    # Holmes is a last name
    name2 = "Mr. Holmes"
    char2_parsed = _HumanName(name2)
    char2_checked = NameParserChecker(name2)
    print(f"{name2}\n")
    print(char2_parsed.as_dict())
    print(char2_checked.as_dict())
    print("==================================")

    # Holmes is a last name
    name3 = "Holmes"
    char3_parsed = _HumanName(name3)
    char3_checked = NameParserChecker(name3)
    print(f"{name3}\n")
    print(char3_parsed.as_dict())
    print(char3_checked.as_dict())
    print("==================================")

    # John is a first name (or nickname)
    name4 = "Mr. John"
    char4_parsed = _HumanName(name4)
    char4_checked = NameParserChecker(name4)
    print(f"{name4}\n")
    print(char4_parsed.as_dict())
    print(char4_checked.as_dict())
