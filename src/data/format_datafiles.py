import unicodedata
import re
import itertools
import os
import string
from collections import defaultdict
from src.tools.path_tools import PathTools
from src.data import make_dataset
import pandas as pd

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

    # male first names
    path = _pt.get_target_dir("data/external/name_list/male_name.txt")
    with open(path, 'r') as f:
        lines = f.readlines()
    male = set()
    for line in lines:
        if line == '\n':
            continue
        line = line.replace("\n", "")
        line = line.capitalize()
        male.add(line)

    # female
    path = _pt.get_target_dir("data/external/name_list/female_name.txt")
    with open(path, 'r') as f:
        lines = f.readlines()
    female = set()
    for line in lines:
        if line == '\n':
            continue
        line = line.replace("\n", "")
        line = line.capitalize()
        female.add(line)

    # female, male = make_dataset.get_namelists()
    surnames -= female
    surnames -= male
    surname_list = list(surnames)
    surname_list.sort()
    new_path = _pt.get_target_dir("data/interim/surnames/surnames_large_unique.txt")
    with open(new_path, 'w') as f:
        for surname in surname_list:
            f.write(f"{surname}\n")

def format_first_names():
    """
    exclude first names that commonly appears as a surname from the first name txt list
    :return:
    """

    # surnames
    path = _pt.get_target_dir('data/external/name_list/surnames.txt')
    with open(path, 'r') as f:
        lines = f.readlines()
    surnames = set()
    for surname in lines:
        if surname == '\n':
            continue
        surname = surname.replace("\n", "")
        surname = surname.capitalize()
        surnames.add(surname)



    path = _pt.get_target_dir("data/external/name_list/male_name.txt")
    with open(path, 'r') as f:
        lines = f.readlines()
    male = set()
    for line in lines:
        if line == '\n':
            continue
        line = line.replace("\n", "")
        line = line.capitalize()
        male.add(line)


    path = _pt.get_target_dir("data/external/name_list/female_name.txt")
    with open(path, 'r') as f:
        lines = f.readlines()
    female = set()
    for line in lines:
        if line == '\n':
            continue
        line = line.replace("\n", "")
        line = line.capitalize()
        female.add(line)

    # exclusion process
    # exclude commonly appearing names in surname list and female list
    male_temp = male.copy()
    male_temp -= surnames
    male_temp -= female
    male_list = list(male_temp)
    male_list.sort()
    new_path = _pt.get_target_dir("data/interim/first_names/male_namelist.txt")
    with open(new_path, 'w') as f:
        for malename in male_list:
            f.write(f"{malename}\n")

    # exclusion process
    # exclude commonly appearing names in surname list and male list
    female_temp = female.copy()

    female_temp -= surnames
    female_temp -= male
    female_list = list(female_temp)
    female_list.sort()
    new_path = _pt.get_target_dir("data/interim/first_names/female_namelist.txt")
    with open(new_path, 'w') as f:
        for femalename in female_list:
            f.write(f"{femalename}\n")

def format_human_ss_csv(path):
    df = pd.read_csv(path)
    print(df.head())

if __name__ == '__main__':
    path = _pt.get_target_dir("data/external/human_ss/stories.csv")
    format_human_ss_csv(path)