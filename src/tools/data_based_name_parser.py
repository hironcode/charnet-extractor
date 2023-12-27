from src.data import make_dataset
from nameparser import HumanName as _HumanName

class NameParserChecker:
    """
    This class compensates nameparser's misidentifications of last name and first name
    by refering to a set of first names and last names
    """
    def __init__(self, name):
        self.name = name
        name_parsed = _HumanName(name).as_dict()
        first = self.check_first(name_parsed)
        last = self.check_last(name_parsed)

        # create instances of corrected name components
        self.title = name_parsed['title']
        if first:
            self.first = first
        else:
            self.first = ''
        if last:
            self.last = last
        else:
            self.last = ''
        self.middle = name_parsed['middle']
        self.suffix = name_parsed['suffix']
        self.nickname = name_parsed['nickname']

    def check_first(self, name_parsed):
        female_names, male_names = make_dataset.get_namelists()
        hypocorisms = set(make_dataset.get_hypocorisms(nicknames_for_names=True).keys())
        first = name_parsed['first']
        if first in female_names or first in male_names or first in hypocorisms:
            # if the parsed name object has a correct first name or nickname (like Em), return the first name
            return first
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
                    return part
            # if no such part, return None, denoting that the full name doesn't have a first name
            return None

    def check_last(self, name_parsed):
        surnames = make_dataset.get_surnames()
        last = name_parsed['last']
        if last in surnames:
            return last
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
                    return part
            # if no such part, return None, denoting that the full name doesn't have a last name
            return None

    def as_dict(self):
        return {
            'title': self.title,
            'first': self.first,
            'middle': self.middle,
            'last': self.last,
            'suffix': self.suffix,
            'nickname': self.nickname
        }

    def __str__(self):
        return str(self.name)
