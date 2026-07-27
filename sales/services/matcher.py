from rapidfuzz import process

from products.models import Product


products = Product.objects.all()

mapping = {

    p.name.lower(): p

    for p in products

}


def find_product(name):

    if not name:

        return None

    hasil = process.extractOne(

        name.lower(),

        mapping.keys()

    )

    if not hasil:

        return None

    nama, score, _ = hasil

    if score < 75:

        return None

    return mapping[nama]