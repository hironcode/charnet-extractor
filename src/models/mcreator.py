import spacy
from src.models import mbank
from spacytextblob.spacytextblob import SpacyTextBlob


def create_spacy_model(title, text, model="en_core_web_trf", update:bool=False) -> (spacy.language.Language, spacy.tokens.doc.Doc):
    """
    Create a spacy model and return it
    :param title: title of the story
    :param text: text of the story
    :param model: type of model to use
    :return:
    """
    nlp = spacy.load(model)
    # add pipeline for sentiment analysis
    nlp.add_pipe("spacytextblob")

    # load doc object
    model_path = mbank.get_spacy_doc_path(title, doc_type=model.replace("en_core_web_", ""))
    if mbank.exists(model_path) and update is False:
        doc = mbank.get_model(model_path)
        print('Pickled model exists!')
    elif update is True:
        doc = nlp(text)
        mbank.save_model(model_path, doc)
        if update is True:
            print("Pickled model is updated.")
        else:
            print("Pickled model didn't exist. Pickled a model.")
    return nlp, doc


