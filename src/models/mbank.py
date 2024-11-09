
# import
import pickle
from src.tools.path_tools import PathTools
from pathlib import Path
import os

# initialize
_pt = PathTools()

# module
def save_model(path, model) -> None:
    """
    Use pickle to convert a model into a binary code
    :param path: path to a model pickle file (the path should contain the model name as well)
    :param model: model to save
    :return: None
    """
    with open(path, 'wb') as f:
        pickle.dump(model, f)


def get_spacy_doc_path(story_title:str, doc_type:str="trf") -> Path:
    """
    Concatenate a path to a spacy model directory and a given title of a story and return an absolute path to the pickle
    :param story_title: title of story
    :return: absolute path to the pickle file of the model of the story
    """
    root_path = f"models/spacy_nlp/spacy_doc_{doc_type}_{story_title}.pickle"
    path = _pt.get_target_dir(root_path)
    return path


def get_model(path):
    with open(path, 'rb') as f:
        model = pickle.load(f)
    return model


def exists(path):
    if type(path) is str:
        path = Path(path)
    parent_dir = path.parent
    files = os.listdir(parent_dir)
    return path.name in files
