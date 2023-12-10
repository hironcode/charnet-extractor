import spacy

import formatting
from character_identification import CharacterIdentification

texts = formatting.format(["test.txt"])

ci = CharacterIdentification(texts["test.txt"])
ci.detect_characters()
result = ci.annotate_gender()
print(result)