from django.core.files.storage import FileSystemStorage

from .ocr import read_receipt
from .parser import parse_receipt


def process_receipt(image):

    storage = FileSystemStorage()

    filename = storage.save(

        image.name,

        image

    )

    text = read_receipt(

        storage.path(filename)

    )

    return parse_receipt(text)