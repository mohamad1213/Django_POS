from decimal import Decimal, InvalidOperation
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.http import JsonResponse
from .models import *

def _safe_decimal(value, default=Decimal('0.00')):
    try:
        return Decimal(str(value)) if value is not None else default
    except (InvalidOperation, TypeError, ValueError):
        return default

def profit_today_value():
    """
    Kembalikan total 'profit hari ini' berdasarkan field tabungan_total jika ada.
    Fallback: kalau tidak ada tabungan_total, hitung per-record:
      tabungan_total = (harga_jual_per_kg * berat_efektif) * (tabungan_persen / 100)
    dimana berat_efektif = berat_input * (1 - susutan_persen/100)
    """
    today = timezone.localtime(timezone.now()).date()

    # Filter untuk tanggal hari ini (compatible DateField / DateTimeField)
    try:
        qs = Profito2.objects.filter(tanggal__date=today)
    except Exception:
        qs = Profito2.objects.filter(tanggal=today)
    # Jika model punya field tabungan_total -> agregasi di DB (paling efisien)
    if hasattr(Profito2, 'tabungan_total'):
        agg = qs.aggregate(total=Sum('tabungan_total'))
        return _safe_decimal(agg.get('total') or 0)

    # Fallback: hitung manual dari tabungan_persen
    total = Decimal('0.00')
    for obj in qs:
        berat = _safe_decimal(getattr(obj, 'berat_input', 0))
        harga_jual = _safe_decimal(getattr(obj, 'harga_jual_per_kg', getattr(obj, 'harga_jual', 0)))
        susutan_persen = _safe_decimal(getattr(obj, 'susutan_persen', 0))
        susutan_frac = (susutan_persen / Decimal('100')) if susutan_persen else Decimal('0.00')
        berat_efektif = berat * (Decimal('1.00') - susutan_frac)

        # Pendapatan kotor per record (harga_jual * berat_efektif)
        pendapatan = harga_jual * berat_efektif

        # Tabungan persen field (mis. 5 berarti 5%)
        tabungan_persen = _safe_decimal(getattr(obj, 'tabungan_persen', 0))
        tabungan_frac = (tabungan_persen / Decimal('100')) if tabungan_persen else Decimal('0.00')

        tabungan_total = pendapatan * tabungan_frac

        total += tabungan_total

    return total.quantize(Decimal('0.01'))


# View yang mengembalikan card render (bisa dipakai langsung dalam template include)
def profit_today_bar(request):
    total = profit_today_value()
    print(total)
    # Format string sederhana untuk template. Sebaiknya format di template.
    context = {
        'profit_today': total,
    }
    return render(request, 'profit/partials/profit_today_bar.html', context)


# OPTIONAL: endpoint JSON untuk AJAX (live refresh)
def profit_today_json(request):
    total = profit_today_value()
    return JsonResponse({
        'profit_today': str(total)  # string agar safe untuk JSON
    })
