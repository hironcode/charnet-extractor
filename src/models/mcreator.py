import spacy
from src.models import mbank
from spacy.tokens import Doc
from spacy.tokens import Span
from spacy.tokens import Token
from spacy.language import Language
from wasabi import msg
from pathlib import Path
# from spacytextblob.spacytextblob import SpacyTextBlob

def create_spacy_model(
        title: str,
        text: str,
        model="en_core_web_trf",
        save_model: bool = False,
        call_old_model: bool = False,
        verbose=False,
    ):
    """
    Create a spacy model and return it
    :param title: title of the story
    :param text: text of the story
    :param model: type of model to use
    :return:
    """

    # set getter for paragraphs
    def get_paragraphs(doc):
        start = 0
        for i, token in enumerate(doc):
            if token.text.count("\n") >= 1 and i > 0:
                # yield Span(self, start, token.i)
                yield doc[start:token.i]
                start = token.i + 1
        yield doc[start:]
        # yield Span(self, start, len(doc))

    # Add custom extension to Doc and Token
    Doc.set_extension("paragraphs", force=True, getter=get_paragraphs)
    Token.set_extension("paragraph_id", default=None, force=True)

    # add custom pipeline component to segment paragraphs
    # @Language.factory("paragraph_segmenter")
    # def paragraph_segmenter(doc):
    #     """
    #     Custom pipeline component to segment paragraphs in a Doc object.
    #     """

    #     id = 0
    #     # Using two newlines as a simple paragraph delimiter
    #     for i, token in enumerate(doc):
    #         doc[i]._.paragraph_id = id
    #         if token.text.count("\n") >= 1 and i > 0:
    #             id += 1
    #     return doc

    # @Language.factory("custom_sentence_boundaries_quote")
    # def custom_sentence_boundaries(doc):
    #     in_quote = False
    #     for token in doc:
    #         if token.is_quote:
    #             in_quote = not in_quote  # Toggle in_quote status on encountering a quote
    #             token.is_sent_start = False  # Prevent a sentence from starting from a quote
    #         elif in_quote:
    #             # Inside a quote, do not start a new sentence
    #             token.is_sent_start = False
    #     return doc

    # @Language.factory("custom_sentence_boundaries_linebreak")
    # def custom_sentence_boundaries_linebreak(doc):
    #     for token in doc:
    #         if token.text.count("\n") >= 1:
    #             token.is_sent_start = True
    #     return doc

    nlp = spacy.load(model)

    # nlp.add_pipe("paragraph_segmenter")
    # nlp.add_pipe("custom_sentence_boundaries_quote", before="parser")
    # nlp.add_pipe("custom_sentence_boundaries_linebreak", before="parser")

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

    if mbank.exists(model_path) and call_old_model is True:
        doc = mbank.get_model(model_path)
        if verbose:
            msg.info('Pickled model exists. Copied the model.\n')
        if save_model is True and verbose:
            msg.info("Pickled model do not need to be saved.\n")
    else:
        if call_old_model is True and verbose:
            msg.info("Pickled model don't exist. Couldn't copy a model.\n")
        doc = nlp(text)
        if save_model is True:
            mbank.save_model(model_path, doc)
            if verbose:
                msg.info("Created a new model. Pickled model is saved.\n")
        elif verbose:
            msg.info("Did't create a new model. Pickled model is not saved.\n")

    return nlp, doc


