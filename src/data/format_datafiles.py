import os

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


if __name__ == '__main__':
    format_titles()