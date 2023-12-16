from src.data import make_dataset
from src.features.character_identification import CharacterIdentification

if __name__ == '__main__':
    texts = make_dataset.format_llm_ss(["test.txt"])

    ci = CharacterIdentification(texts["test.txt"])
    ci.detect_characters()
    result = ci.annotate_gender()
    print(result)