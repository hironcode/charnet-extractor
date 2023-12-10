import spacy
import os


def format():
    texts = {}

    ai_dir_path = "./txt_files/AI"
    human_dir_path = "./txt_files/Human"

    titles = [
        f for f in os.listdir(ai_dir_path) if os.path.isfile(os.path.join(ai_dir_path, f))
    ]
    titles.remove("test.txt")

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