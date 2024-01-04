import unicodedata
import re
import itertools
import os
import string
from collections import defaultdict
from src.tools.path_tools import PathTools
from src.data import make_dataset

_pt = PathTools()


def format_titles(files:list=["female_honorific_titles.txt", "male_honorific_titles.txt"]):
    filedir = "../../data/raw/titles/"
    female = set()
    male = set()

    for file in files:
        if "female" in file.lower():
            title_set = female
        elif "male" in file.lower():
            title_set = male

        path = os.path.join(filedir, file)
        with open(path, 'r') as f:
            lines = f.readlines()
        for line in lines:
            # if the line is just a newline command, remove it from the text
            if line == "\n":
                continue
            # replace specified signs with a corresponding str
            title_set.add(line)
    unique_female = female - male
    unique_male = male - female
    print(unique_female)
    print(unique_male)

    write_dir = "../../data/interim/unique_titles/"
    unique_files = {
        "female_honorific_titles.txt": unique_female,
        "male_honorofic_titles.txt": unique_male,
    }
    for file, var in unique_files.items():
        path = os.path.join(write_dir, file)
        with open(path, 'w') as f:
            for title in var:
                f.write(title)


def remove_accents(input_str):
    # Normalize the string to decompose the accented characters
    nfkd_form = unicodedata.normalize('NFKD', input_str)

    # Create a string without the diacritics
    only_ascii = nfkd_form.encode('ASCII', 'ignore')

    return only_ascii.decode('utf-8')


# reference:
# https://stackoverflow.com/questions/58353516/replace-all-except-the-first-occurrence-of-a-substring-in-python
def replace_second_or_later(text, word):
    c = itertools.count()
    r = re.sub(rf"\b{word}\b", lambda x: x.group() if not next(c) else '', text)
    return r

def format_hypocorisms(reverse:bool=True):
    """
    :return: dict{ALPHABETS: dict{NAMES: [HYPOCORISMS]}}
    :return(reverse=True): dict{ALPHABETS: dict{HYPOCORISMS: [NAMES]}}
    I manually replaced hyphens in the line of Stephen and Steven
    I manually replaced a hypen in "Zo-Zo"
    """

    path = "../../data/external/name_list/hypocorism_name.txt"
    hypocorisms = {}
    abc = set(string.ascii_uppercase)
    if reverse is True:
        # initialize hypocorism dict
        for alphabet in abc:
            hypocorisms[alphabet] = defaultdict(list)
    elif reverse is False:
        # initialize hypocorism dict
        for alphabet in abc:
            hypocorisms[alphabet] = {}

    with open(path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        # # if the line is just a newline command, remove it from the text
        # if line == "\n":
        #     continue
        # remove a line break
        line = line.replace("\n", "")

        # if the line has only an alphabetical letter or no hypocricorisms, skip it
        if "," not in line and "-" not in line:
            continue

        # remove accented alphabets
        # line = remove_accents(line)

        # remove spaces
        line = line.replace(" ", "")

        # remove the last comma in some lines:
        line = line.rstrip(",")

        # some lines have "/ (slash)" to indicate different strings with the similar pronunciation
        # replace "/" with "," for the future convenience
        line = line.replace("/", ",")

        # replace "(" " => ","; and ")" => "" to convert parentices into a comma
        line = line.replace("(", ",")
        line = line.replace(")", "")

        # replace the second and later hypens with underscores
        # (do not replace the first hypen since it partitions name and nicknames)
        line = replace_second_or_later(line, "-")

        # the format is => "NAME - HYPOCORISM1, HYPOCORISM2, ..."
        # split the line into a name and a list of hypocorisms by replacing "-" just one time (the leftmost hyphen)
        line = line.split(sep="-", maxsplit=1)

        # the line should have at least one hypocorism. If the righthand side has more than 1 element, split it
        if "," in line[1]:
            line[1] = line[1].split(sep=",")
        # if not, put the unique element in a list
        else:
            line[1] = [line[1]]

        if reverse is True:
            name = line[0]
            for hypo in line[1]:
                initial = hypo.upper()[0]
                hypocorisms[initial][hypo].append(name)

        elif reverse is False:
            # fetch the initial letter of the name
            name = line[0]
            initial = name.upper()[0]
            # assign the hypocrisms by
            # (1) searching the initial in the dict;
            # (2) create a tab of the name; and
            # (3) assigning the list of hypocrisms
            hypocorisms[initial][name] = line[1]

    # create a formatted txt file
    folder_dir = "../../data/interim/hypocorisms/"
    if reverse is False:
        with open(os.path.join(folder_dir, "hypocorisms_name_for_nicknames.txt"), 'w') as f:
            # for each alphabet
            for _, name_nicknames in hypocorisms.items():
                # and for each name and nickname
                for name in name_nicknames.keys():
                    for nickname in name_nicknames[name]:
                        f.write(f"{name}@{nickname}\n")
    elif reverse is True:
        with open(os.path.join(folder_dir, "hypocorisms_nickname_for_names.txt"), 'w') as f:
            # for each alphabet
            for _, name_nicknames in hypocorisms.items():
                # and for each name and nickname
                for nickname in name_nicknames.keys():
                    for name in name_nicknames[nickname]:
                        f.write(f"{nickname}@{name}\n")


def format_surnames():
    """
    exclude surnames that commonly appears as first names from the large surname txt list
    :return:
    """
    path = _pt.get_target_dir('data/external/name_list/surnames_large.txt')
    with open(path, 'r') as f:
        lines = f.readlines()
    surnames = set()
    for surname in lines:
        if surname == '\n':
            continue
        surname = surname.replace("\n", "")
        surname = surname.capitalize()
        surnames.add(surname)
    female_names, male_names = make_dataset.get_namelists()
    surnames -= female_names
    surnames -= male_names
    surname_list = list(surnames)
    surname_list.sort()
    new_path = _pt.get_target_dir("data/interim/surnames/surnames_large_unique.txt")
    with open(new_path, 'w') as f:
        for surname in surname_list:
            f.write(f"{surname}\n")


def format_llm_ss(file:list="all"):
    texts = {}

    dir_path = _pt.get_target_dir("data/raw/llm_ss")

    if file == "all":
        titles = [
            f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
        ]
    else:
        titles = file

    # signs to remove and alternative string to be replaced to
    signs = {
        "\n": " ",
        "\t": "",
    }

    for title in titles:
        path = os.path.join(dir_path, title)
        with open(path, 'r') as f:
            textlines = f.readlines()

        # initialize the dict
        texts[title] = ""
        for line in textlines:
            # if the line is a separate line, remove it
            if line == "---":
                continue

            # replace specified signs with a corresponding str
            for key, val in signs.items():
                line = line.replace(key, val)
            texts[title] += line
    return texts


if __name__ == '__main__':
    format_hypocorisms(reverse=False)
