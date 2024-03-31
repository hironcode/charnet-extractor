import spacy
from src.models import mbank
from spacy.tokens import Doc
from spacy.tokens import Span
from spacy.tokens import Token
from spacy.language import Language
from wasabi import msg
# from spacytextblob.spacytextblob import SpacyTextBlob


def create_spacy_model(
        title: str,
        text: str,
        model="en_core_web_trf",
        save_update:bool=False
    ) -> (Language, Doc):
    """
    Create a spacy model and return it
    :param title: title of the story
    :param text: text of the story
    :param model: type of model to use
    :return:
    """
    # Add custom extension to Doc and Token
    Token.set_extension("paragraph_id", default=None, force=True)
    Doc.set_extension("paragraphs", default=[], force=True)

    # add custom pipeline component to segment paragraphs
    @Language.component("paragraph_segmenter")
    def paragraph_segmenter(doc):
        """
        Custom pipeline component to segment paragraphs in a Doc object.
        """

            # paragraph segmenter

        start = 0
        paragraphs = []
        id = 0
        skip = True

        # Using two newlines as a simple paragraph delimiter
        for i, token in enumerate(doc):
            doc[i]._.paragraph_id = id
            
            if token.text.count("\n") >= 1 and i > 0:
                span = doc[start:token.i]
                msg.info(token)
                msg.good(span.text.strip())
                if len(span.text.strip()) > 0:
                    paragraphs.append(span)
                start = token.i + 1
                id += 1

        # Catch any remaining document text as a final paragraph
        if start < len(doc):
            paragraphs.append(doc[start:len(doc)])

        doc._.paragraphs = paragraphs
        return doc

    nlp = spacy.load(model)
    # add pipeline for sentiment analysis
    # nlp.add_pipe("spacytextblob")

    # add special cases for every chapter markers enclosed in square brackets: like [c1]
    # this is to prevent the model from splitting the chapter markers into separate tokens
    # Reference: https://stackoverflow.com/questions/76255486/how-to-stop-spacy-tokenizer-from-tokenizing-words-enclosed-within-brackets

    nlp.add_pipe("paragraph_segmenter")

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


