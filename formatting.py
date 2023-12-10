import spacy
import os


def format(file:list="all"):
    texts = {}

    ai_dir_path = "./txt_files/AI"
    human_dir_path = "./txt_files/Human"

    if file == "all":
        titles = [
            f for f in os.listdir(ai_dir_path) if os.path.isfile(os.path.join(ai_dir_path, f))
        ]
    else:
        titles = file

    # signs to remove and alternative string to be replaced to
    signs = {
        "\n": " ",
        "\t": ""
    }

    current_directory = "txt_files/AI/"

    for title in titles:
        path = current_directory + title
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

    male_path = "./src/name/male_name.txt"
    with open(male_path, 'r') as f:
        male_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    male_lines = list(map(lambda x: x.replace("\n", ""), male_lines[7:]))
    # put the list in a set to do hash search in the future
    male_names = set(male_lines)

    female_path = "./src/name/female_name.txt"
    with open(female_path, 'r') as f:
        female_lines = f.readlines()
    # list of names begins in the line 8 in both the text files
    female_lines = list(map(lambda x: x.replace("\n", ""), female_lines[7:]))
    # put the list in a set to do hash search in the future
    female_names = set(female_lines)

    return male_names, female_names
