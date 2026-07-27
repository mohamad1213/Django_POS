import re


def clean_text(text):

    replace = {

        "©": "@",
        "€": "@",
        "¢": "@",
        "a": "@",

    }

    for old, new in replace.items():
        text = text.replace(old, new)

    text = re.sub(r'[ ]{2,}', ' ', text)

    return text