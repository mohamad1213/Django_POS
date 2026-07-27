import pytesseract

from django.conf import settings

from .preprocess import preprocess

pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def read_receipt(image_path):

    img = preprocess(image_path)

    config = (
        "--oem 3 "
        "--psm 4 "
        "-c preserve_interword_spaces=1"
    )

    return pytesseract.image_to_string(
        img,
        lang="ind+eng",
        config=config
    )