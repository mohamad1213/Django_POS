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

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def sales_list_view(request):
    context = {
        "active_icon": "sales",
        "sales": Sale.objects.all().order_by('-date_added')
    }
    return render(request, "sales/sales.html", context=context)


@login_required(login_url="/accounts/login/")
def sales_add_view(request):
    context = {
        "active_icon": "sales",
        "customers": [c.to_select2() for c in Customer.objects.all()]
    }

    if request.method == 'POST':
        if is_ajax(request=request):
            # Save the POST arguments
            data = json.load(request)

            sale_attributes = {
                "customer": Customer.objects.get(id=int(data['customer'])),
                "sub_total": float(data["sub_total"]),
                "amount_payed": float(data["amount_payed"]),
                "amount_change": float(data["amount_change"]),

            }
            try:
                new_sale = Sale.objects.create(**sale_attributes)
                new_sale.save()
                products = data["products"]

                for product in products:
                    detail_attributes = {
                        "sale": Sale.objects.get(id=new_sale.id),
                        "product": Product.objects.get(id=int(product["id"])),
                        "price": product["price"],
                        "quantity": product["quantity"],
                        "total_detail": product["total_product"]
                    }
                    sale_detail_new = SaleDetail.objects.create(**detail_attributes)
                    sale_detail_new.save()
                    
                response_data = {'success': True, 'message': 'Sale successfully created!', 'redirect_url': '/sales/'}

            except Exception as e:
                response_data = {'success': False, 'message': 'There was an error during the creation!'}

            return JsonResponse(response_data)

    return render(request, "sales/sales_add.html", context=context)


@login_required(login_url="/accounts/login/")
def sales_details_view(request, sale_id):
    try:
        # Get the sale
        sale = Sale.objects.get(id=sale_id)

        # Get the sale details
        details = SaleDetail.objects.filter(sale=sale)

        context = {
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

def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None
# @login_required(login_url="/accounts/login/")
# def receipt_pdf_view(request, sale_id):
#     # Get the sale
#     sale = Sale.objects.get(id=sale_id)

#     # Get the sale details
#     details = SaleDetail.objects.filter(sale=sale)

#     data = {
#         "sale": sale,
#         "details": details
#     }

#     return render(request, "sales/sales_receipt_pdf.html", context=data)

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
