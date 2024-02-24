import spacy
from src.models import mbank
# from spacytextblob.spacytextblob import SpacyTextBlob


def create_spacy_model(
        title: str,
        text: str,
        model="en_core_web_trf",
        save_update:bool=False
    ) -> (spacy.language.Language, "spacy.tokens.doc.Doc"):
    """
    Create a spacy model and return it
    :param title: title of the story
    :param text: text of the story
    :param model: type of model to use
    :return:
    """

    nlp = spacy.load(model)
    # add pipeline for sentiment analysis
    # nlp.add_pipe("spacytextblob")

    # add special cases for every chapter markers enclosed in square brackets: like [c1]
    # this is to prevent the model from splitting the chapter markers into separate tokens
    # Reference: https://stackoverflow.com/questions/76255486/how-to-stop-spacy-tokenizer-from-tokenizing-words-enclosed-within-brackets

    # Add the special case rule
    infixes = nlp.Defaults.infixes + [r"([\[\]])"]
    nlp.tokenizer.infix_finditer = spacy.util.compile_infix_regex(infixes).finditer
    tags = [f"c{chap}" for chap in range(1, 51)]
    # Add the special cases to the tokenizer
    for tag in tags:
        nlp.tokenizer.add_special_case(f"[{tag}]", [{"ORTH": f"[{tag}]"}])

    # load doc object
    model_path = mbank.get_spacy_doc_path(title, doc_type=model.replace("en_core_web_", ""))
    if mbank.exists(model_path):
        doc = mbank.get_model(model_path)
        print('Pickled model existed. Copied the model.\n')
        if save_update is True:
            print("New model is not created, so the pickled model is not saved or updated.")
        else:
            pass
    else:
        doc = nlp(text)
        print("Pickled model didn't exist. Created a new model.\n")
        if save_update is True:
            mbank.save_model(model_path, doc)
            print("Pickled model is saved and updated.")
        else:
            pass
    return nlp, doc


