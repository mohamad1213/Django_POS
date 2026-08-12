import os

from django.core.files.storage import FileSystemStorage

from .ocr import read_receipt
from .parser import parse_receipt


def process_receipt(image):
    storage = FileSystemStorage()
    filename = storage.save(image.name, image)
    filepath = storage.path(filename)

    try:
        text = read_receipt(filepath)
        return parse_receipt(text)
    finally:
        # Hapus file gambar setelah diproses agar tidak menumpuk di server
        if os.path.exists(filepath):
            os.remove(filepath)