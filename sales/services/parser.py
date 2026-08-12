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


def _parse_number(s):
    """Hapus titik ribuan dan konversi ke int."""
    return int(s.replace(".", "").replace(",", ""))


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
                result["total"] = _parse_number(angka[-1])
            continue

        # skip metadata
        if any(k in upper for k in SKIP):
            continue

        # Format 1: qty @ harga subtotal  (contoh: "5 @ 1.900 9.500")
        match = re.search(
            r'(\d+)\s*[@xX]\s*([\d\.]+)\s+([\d\.]+)',
            line
        )
        if match:
            qty     = int(match.group(1))
            harga   = _parse_number(match.group(2))
            subtotal = _parse_number(match.group(3))
            result["items"].append({
                "name": current_name,
                "qty": qty,
                "price": harga,
                "subtotal": subtotal
            })
            current_name = None
            continue

        # Format 2: harga subtotal pada baris yang sama (tanpa separator @/x)
        # Contoh baris: "Rp 1.900  Rp 771.400"  atau  "1.900 771.400"
        # Qty dihitung: round(subtotal / harga)
        match2 = re.search(
            r'(?:Rp\.?\s*)?([\d]{1,3}(?:\.[\d]{3})+|[\d]+)\s+(?:Rp\.?\s*)?([\d]{1,3}(?:\.[\d]{3})+|[\d]{4,})',
            line
        )
        if match2 and current_name:
            harga    = _parse_number(match2.group(1))
            subtotal = _parse_number(match2.group(2))

            if harga > 0 and subtotal >= harga:
                qty = round(subtotal / harga)
            else:
                qty = 1

            result["items"].append({
                "name": current_name,
                "qty": qty,
                "price": harga,
                "subtotal": subtotal
            })
            current_name = None
            continue

        # nama barang (baris tanpa angka panjang)
        if not re.search(r'\d{4,}', line):
            current_name = line

    return result