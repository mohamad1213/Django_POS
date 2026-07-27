import re

from .utils import clean_text


SKIP = [

    "TOTAL",
    "BAYAR",
    "SISA",
    "TERIMAKASIH",
    "PRINTED",
    "CATATAN",
    "TANGGAL",
    "TELP",
    "ALAMAT",
    "QTY",

]


def parse_receipt(text):

    text = clean_text(text)

    result = {

        "items": [],
        "total": 0,
        "raw": text

    }

    lines = [

        x.strip()

        for x in text.splitlines()

        if x.strip()

    ]

    current_name = None

    for line in lines:

        upper = line.upper()

        # TOTAL

        if upper.startswith("TOTAL"):

            angka = re.findall(r'[\d\.]+', line)

            if angka:

                result["total"] = int(
                    angka[-1].replace(".", "")
                )

            continue

        # skip metadata

        if any(k in upper for k in SKIP):

            continue

        # qty harga subtotal

        match = re.search(

            r'(\d+)\s*[@xX]\s*([\d\.]+)\s+([\d\.]+)',

            line

        )

        if match:

            qty = int(match.group(1))

            harga = int(match.group(2).replace(".", ""))

            subtotal = int(match.group(3).replace(".", ""))

            result["items"].append({

                "name": current_name,

                "qty": qty,

                "price": harga,

                "subtotal": subtotal

            })

            current_name = None

            continue

        # nama barang

        if not re.search(r'\d{4,}', line):

            current_name = line

    return result