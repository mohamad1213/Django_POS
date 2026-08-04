from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
import sweetify

from .models import Afkiran, AfkiranDetail, JENIS_BARANG_CHOICES
from sales.models import Sale, SaleDetail

from django.http import HttpResponse
from django.views.generic import View


@login_required
def afkiran_list(request):
    status_filter = request.GET.get('status', 'ALL')
    afkiran_qs = Afkiran.objects.all().select_related('sale', 'owner', 'sale__customer').order_by('-date_created')

    if status_filter in ['PENDING', 'LUNAS']:
        afkiran_qs = afkiran_qs.filter(status=status_filter)

    total_afkiran = afkiran_qs.count()
    total_sortir = afkiran_qs.aggregate(Sum('total_sortir'))['total_sortir__sum'] or 0
    total_sisa_bayar = afkiran_qs.filter(status='PENDING').aggregate(Sum('sisa_bayar'))['sisa_bayar__sum'] or 0

    context = {
        'afkiran_list': afkiran_qs,
        'status_filter': status_filter,
        'total_afkiran': total_afkiran,
        'total_sortir': total_sortir,
        'total_sisa_bayar': total_sisa_bayar,
    }
    return render(request, 'afkiran/afkiran_list.html', context)


@login_required
def afkiran_create(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Cek jika sale sudah pernah di-afkir
    if sale.is_afkiran or hasattr(sale, 'afkiran'):
        sweetify.warning(request, 'Nota Ini Sudah Di-afkir!', text='Satu nota hanya dapat di-afkir 1 kali.')
        return redirect('afkiran:afkiran_detail', afkiran_id=sale.afkiran.id)

    if request.method == 'POST':
        try:
            dp_amount = float(request.POST.get('dp_amount', 0) or 0)
        except ValueError:
            dp_amount = 0.0

        catatan = request.POST.get('catatan', '').strip()

        afkiran = Afkiran.objects.create(
            sale=sale,
            owner=request.user,
            dp_amount=dp_amount,
            total_nota=sale.sub_total,
            catatan=catatan,
            status='PENDING'
        )

        for code, label in JENIS_BARANG_CHOICES:
            qty_str = request.POST.get(f'qty_{code}', '0')
            harga_str = request.POST.get(f'harga_{code}', '0')

            try:
                qty = float(qty_str or 0)
            except ValueError:
                qty = 0.0

            try:
                harga = float(harga_str or 0)
            except ValueError:
                harga = 0.0

            AfkiranDetail.objects.create(
                afkiran=afkiran,
                nama_barang=code,
                quantity=qty,
                harga=harga
            )

        # Hitung kalkulasi akhir
        afkiran.recalculate()

        # Update model sale
        sale.is_afkiran = True
        sale.dp_amount = dp_amount
        sale.save(update_fields=['is_afkiran', 'dp_amount'])

        sweetify.success(request, 'Berhasil!', text='Hasil afkiran berhasil disimpan.')
        messages.success(request, f'Afkiran Nota #{sale.transaction_number} berhasil disimpan.')
        return redirect('afkiran:afkiran_detail', afkiran_id=afkiran.id)

    context = {
        'sale': sale,
        'jenis_barang_choices': JENIS_BARANG_CHOICES,
    }
    return render(request, 'afkiran/afkiran_form.html', context)


@login_required
def afkiran_detail(request, afkiran_id):
    afkiran = get_object_or_404(Afkiran.objects.select_related('sale', 'owner', 'sale__customer'), id=afkiran_id)
    details = afkiran.afkirandetail_set.all()

    context = {
        'afkiran': afkiran,
        'details': details,
    }
    return render(request, 'afkiran/afkiran_detail.html', context)


@login_required
def afkiran_settle(request, afkiran_id):
    if request.method == 'POST':
        afkiran = get_object_or_404(Afkiran, id=afkiran_id)
        if afkiran.status != 'LUNAS':
            afkiran.status = 'LUNAS'
            afkiran.save(update_fields=['status'])
            sweetify.success(request, 'Lunas!', text='Status Afkiran kini menjadi LUNAS.')
            messages.success(request, f'Afkiran Nota #{afkiran.sale.transaction_number} diselesaikan (LUNAS).')
        return redirect('afkiran:afkiran_detail', afkiran_id=afkiran.id)
    return redirect('afkiran:afkiran_list')

def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None
class ViewPDF(View):
    def get(self, request, afkiran_id, *args, **kwargs,):
        afkiran = get_object_or_404(Afkiran, id=afkiran_id)
        details = AfkiranDetail.objects.filter(afkiran=afkiran, quantity__gt=0)

        data = {
            "sale": afkiran.sale,
            "afkiran": afkiran,
            "details": details
        }

        pdf = render_to_pdf('afkiran/afkiran_recipe.html', data)
        return HttpResponse(pdf, content_type='application/pdf')
