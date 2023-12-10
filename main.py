import spacy

import formatting
from character_identification import CharacterIdentification

texts = formatting.format()
# for text in texts.values():
#     ci = CharacterIdentification(text)
#     ci.detect_characters()
#     print(ci.chars)

ci = CharacterIdentification(texts["totally_test.txt"])
ci.detect_characters()
ci.annotate_gender()
print(ci.chars)
