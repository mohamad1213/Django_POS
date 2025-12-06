import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from zeta.wsgi import *
from zeta import settings
import sweetify
from django.template.loader import get_template
from customers.models import Customer
from products.models import Product
from .models import Sale, SaleDetail
import json
from io import BytesIO
from xhtml2pdf import pisa
from django.views import View
from django.http import JsonResponse
from zetaapp.models import Transaksi
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def sales_list_view(request):
    salesa = Sale.objects.filter(owner=request.user)  # Query utama

    totals = salesa.aggregate(
        total_transactions=Count('id'),
        total_items=Sum('saledetail__quantity'),
        total_revenue=Sum('sub_total'),
    )

    context = {
        "breadcrumb": {"parent": "POS", "child": "Point Of Sale"},
        "active_icon": "sales",
        "sales": Sale.objects.all().order_by('-id'),
        'salesa': salesa,
        'totals': totals,
    }
    return render(request, "sales/sales.html", context=context)



@login_required(login_url="/accounts/login/")
def sales_add_view(request):
    customers = [c.to_select2() for c in Customer.objects.all()]

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            customer_obj = None
            new_name = data.get('new_customer_name', '').strip()
            new_address = data.get('new_customer_address', '').strip()
            new_phone = data.get('new_customer_phone', '').strip()
            if new_name:
                customer_obj, created = Customer.objects.get_or_create(
                    first_name=new_name,
                    defaults={
                        'address': new_address,
                        'phone': new_phone
                    }
                )
            else:
                customer_id = data.get('customer')
                if customer_id:
                    customer_obj = Customer.objects.get(id=int(customer_id), owner=request.user)

            
            sub_total = float(data['sub_total'])
            amount_payed = float(data['amount_payed'])
            amount_change = float(data['amount_change'])

            new_sale = Sale.objects.create(
                owner=request.user,
                customer=customer_obj,
                sub_total=sub_total,
                amount_payed=amount_payed,
                amount_change=amount_change
            )

            for product in data['products']:
                SaleDetail.objects.create(
                    sale=new_sale,
                    product=Product.objects.get(id=int(product['id'])),
                    price=float(product['price']),
                    quantity=int(product['quantity']),
                    total_detail=float(product['total_product'])
                )

            response_data = {
                'success': True,
                'message': 'Transaksi berhasil dibuat!',
                'redirect_url': '/sales/'  # Ganti sesuai URL list transaksi
            }

        except Exception as e:
            response_data = {
                'success': False,
                'message': f'Terjadi kesalahan: {str(e)}'
            }

        return JsonResponse(response_data)

    context = {
        "breadcrumb": {"parent": "POS", "child": "Point Of Sale"},
        "active_icon": "sales",
        "customers": customers
    }
    return render(request, "sales/sales_add.html", context=context)



@login_required(login_url="/accounts/login/")
def sales_details_view(request, sale_id):
    try:
        # Get the sale
        sale = Sale.objects.get(id=sale_id, owner=request.user)

        # Get the sale details
        details = SaleDetail.objects.filter(sale=sale)

        context = {
            "breadcrumb": {"parent": "POS", "child": "Point Of Sale"},
        
            "active_icon": "sales",
            "sale": sale,
            "details": details,
        }
        return render(request, "sales/sales_details.html", context=context)
    except Exception as e:
        sweetify.success(
            request, 'There was an error getting the sale!', extra_tags="danger")
        print(e)
        return redirect('sales:sales_list')

@login_required(login_url="/accounts/login/")
def delete_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id, owner=request.user)

    if request.method == "POST":
        # Hapus semua detail transaksi
        SaleDetail.objects.filter(sale=sale).delete()
        sale.delete()

        messages.success(request, "Transaksi berhasil dihapus!")
        return redirect('sales:sales_list')  # ganti sesuai nama URL list transaksi

    # Jika bukan POST, redirect saja
    messages.error(request, "Invalid request.")
    return redirect('sales:sales_list')

def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None

class ViewPDF(View):
    def get(self, request, sale_id, *args, **kwargs,):
        sale = Sale.objects.get(id=sale_id)

        # Get the sale details
        details = SaleDetail.objects.filter(sale=sale)

        data = {
            "sale": sale,
            "details": details
        }


        pdf = render_to_pdf('sales/sales_receipt_pdf.html', data)
        return HttpResponse(pdf, content_type='application/pdf')
