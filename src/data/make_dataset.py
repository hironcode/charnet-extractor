import os
import string
from collections import defaultdict
from src.data import format_datafiles
from src.tools.path_tools import PathTools
_pt = PathTools()
import re

def format_ss(dir_path, file="all") -> dict:
    """
    :param dir_path: path to the parent directory containing the story folders (i.e. "data/ss/llm_ss/Gemini 2.0 Flash")

    """

    texts = {}

    if file == "all":
        titles = [
            title for title in os.listdir(dir_path) if os.path.isdir(dir_path/title)
        ]
    else:
        titles = file

    # signs to remove and alternative string to be replaced to
    signs = {
        # "\n": " ",
        "\t": "",
        "*": "",
        "#": "",
    }

    for title in titles:
        path = dir_path/title/"story.txt"
        with open(path, 'r') as f:
            textlines = f.readlines()

        # format title, removing the extension
        title = title.split(".")[0]

        # initialize the dict
        texts[title] = ""
        for i, line in enumerate(textlines):
            
            conditions = [
                line == '\n',
                re.search("---", line),
                re.search("##", line),
                #re.search(r"<c\d+>", line),
            ]

            if True in conditions:
                continue
            
            # remove the title line of LLM stories
            if "llm_ss" in str(dir_path) and i == 0:
                continue

            # replace specified signs with a corresponding str
            if not re.search(r"<c\d+>", line):
                for key, val in signs.items():
                    line = line.replace(key, val)
            texts[title] += line
    return texts


def format_human_ss(file:list="all"):
    texts = {}

    dir_path = _pt.get_target_dir("data/external/human_ss")

    if file == "all":
        titles = [
            f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
        ]
    else:
        titles = file

    # signs to remove and alternative string to be replaced to
    signs = {
        # "\n": " ",
        "\t": ""
    }

    for title in titles:
        path = os.path.join(dir_path, title)
        with open(path, 'r') as f:
            textlines = f.readlines()

        # initialize the dict
        texts[title] = ""
        for line in textlines:
            # if the line is just a newline command, remove it from the text
            if line == "\n":
                continue
            # replace specified signs with a corresponding str
            for key, val in signs.items():
                line = line.replace(key, val)
            texts[title] += line

    return texts


def get_namelists():

    male_path = _pt.get_target_dir("data/interim/first_names/male_namelist.txt")

    with open(male_path, 'r') as f:
        male_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    male_lines = list(map(lambda x: x.replace("\n", ""), male_lines[7:]))
    # put the list in a set to do hash search in the future
    male_names = set(male_lines)

    female_path = _pt.get_target_dir("data/interim/first_names/female_namelist.txt")
    with open(female_path, 'r') as f:
        female_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    female_lines = list(map(lambda x: x.replace("\n", ""), female_lines[7:]))
    # put the list in a set to do hash search in the future
    female_names = set(female_lines)

    return female_names, male_names


def get_titles() -> tuple[set, set, set]:
    """
    :return: set of female titles and set of male titles. The elements in the sets does not contain a period, capitalized.
    """
    # female_path = "../data/interim/unique_titles/female_honorific_titles.txt"
    female_path = _pt.get_target_dir("data/interim/unique_titles/female_honorific_titles.txt")
    with open(female_path, 'r') as f:
        female_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    female_lines = list(map(lambda x: x.replace("\n", ""), female_lines))
    # remove periods after each title and make them lowercase
    female_lines = list(map(lambda x: x.replace(".", ""), female_lines))
    # female_lines = list(map(lambda x: x.lower(), female_lines))
    # put the list in a set to do hash search in the future
    female_lines = [e for e in female_lines if e != ""]
    female_titles = set(female_lines)

    # male_path = "../data/interim/unique_titles/male_honorofic_titles.txt"
    male_path = _pt.get_target_dir("data/interim/unique_titles/male_honorific_titles.txt")
    with open(male_path, 'r') as f:
        male_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    male_lines = list(map(lambda x: x.replace("\n", ""), male_lines))
    # remove periods after each title and make them lowercase
    male_lines = list(map(lambda x: x.replace(".", ""), male_lines))
    # male_lines = list(map(lambda x: x.lower(), male_lines))
    # put the list in a set to do hash search in the future
    male_lines = [e for e in male_lines if e != ""]
    male_titles = set(male_lines)

    # common_path = "../data/interim/unique_titles/common_honorific_titles.txt"
    common_path = _pt.get_target_dir("data/interim/unique_titles/common_honorific_titles.txt")
    with open(common_path, 'r') as f:
        common_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    common_lines = list(map(lambda x: x.replace("\n", ""), common_lines))
    # remove periods after each title and make them lowercase
    common_lines = list(map(lambda x: x.replace(".", ""), common_lines))
    # common_lines = list(map(lambda x: x.lower(), common_lines))
    # put the list in a set to do hash search in the future
    common_lines = [e for e in common_lines if e != ""]

    common_titles = set(common_lines)

    return female_titles, male_titles, common_titles


def get_hypocorisms(nicknames_for_names:bool=True):
    """
    The initials are upper-case, the names are capitalized, and the hypocorisms are also capitalized.

    :return: dict{INITIALS: dict{Names: [Hypocorisms]}}
    :return(reverse=True): dict{INITIALS: dict{Hypocorisms: [Names]}}

    """

    abc = set(string.ascii_uppercase)
    hypocorisms = {
        initial: defaultdict(list) for initial in abc
    }

    if nicknames_for_names is True:
        path = _pt.get_target_dir("data/interim/hypocorisms/hypocorisms_nickname_for_names.txt")
    elif nicknames_for_names is False:
        path = _pt.get_target_dir("data/interim/hypocorisms/hypocorisms_name_for_nicknames.txt")
    else:
        ValueError("For reverse, only boolen values are accepted")

    with open(path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        # if the line is just a newline command, remove it from the text
        if line == "\n":
            continue
        # remove a line break
        line = line.replace("\n", "")

        root_branch_list = line.split("@")
        root = root_branch_list[0]
        branch = root_branch_list[1]
        initial = root.upper()[0]

        hypocorisms[initial][root].append(branch)
    return hypocorisms

def get_surnames():
    """
    This returns a set of surnames that also include commonly used first names
    :return:
    """
    path = _pt.get_target_dir('data/interim/surnames/surnames_unique.txt')
    with open(path, 'r') as f:
        lines = f.readlines()
    surnames = set()
    for surname in lines:
        if surname == '\n':
            continue
        surname = surname.replace("\n", "")
        surname = surname.capitalize()
        surnames.add(surname)
    female_names, male_names = get_namelists()
    surnames -= female_names
    surnames -= male_names
    return surnames
