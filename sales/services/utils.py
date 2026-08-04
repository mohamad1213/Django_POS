import re


def clean_text(text):

    replace = {

        "©": "@",
        "€": "@",
        "¢": "@",

    }

    for old, new in replace.items():
        text = text.replace(old, new)
    text = re.sub(r'(?<=[a-zA-Z])@(?=[a-zA-Z])', 'a', text)
    text = re.sub(r'[ ]{2,}', ' ', text)

    return text