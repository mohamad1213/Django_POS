import os
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from zeta import settings
import sweetify
from django.template.loader import get_template
from customers.models import Customer
from products.models import Product
from products.models import Category
from .models import Sale, SaleDetail
import json
from io import BytesIO
from xhtml2pdf import pisa
from django.views import View
from django.http import JsonResponse
from django.db.models import Sum, Count, F
from zetaapp.models import Transaksi, Stock
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from sales.services.ocr_services import process_receipt
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.db.models import F
from .models import Sale, SaleDetail, Product, Customer
from django.core.paginator import Paginator


def upload_receipt(request):

    if request.method != "POST":
        return redirect("sales:sales_list")

    image = request.FILES.get("file_transaksi")

    if not image:
        messages.error(request, "Silakan pilih gambar.")
        return redirect("sales:sales_list")

    result = process_receipt(image)

    if not result["items"]:
        messages.warning(request, "Produk tidak berhasil dideteksi.")

    request.session["ocr_result"] = result

    return redirect("sales:preview_receipt")
def preview_receipt(request):
    return render(
        request,
        "sales/preview_receipt.html",
        {
            "breadcrumb": {"parent": "POS", "child": "Preview Hasil OCR"},
            "active_icon": "sales",
            "data": request.session.get("ocr_result"),
        },
    )
def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def sales_list_view(request):
    salesa = Sale.objects.filter(owner=request.user)  # Query utama

    totals = salesa.aggregate(
        total_transactions=Count('id'),
        total_items=Sum('saledetail__quantity'),
        total_revenue=Sum('sub_total'),
        total_paid=Sum('amount_payed'),
    )

    # Pagination – 20 transaksi per halaman
    sales_qs = salesa.order_by('-id')
    paginator = Paginator(sales_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "breadcrumb": {"parent": "POS", "child": "Point Of Sale"},
        "active_icon": "sales",
        "sales": page_obj,          # paginated queryset
        "page_obj": page_obj,
        'salesa': salesa,
        'totals': totals,
    }
    return render(request, "sales/sales.html", context=context)
@login_required(login_url="/accounts/login/")
def sales_add_view(request):
    customers = [c.to_select2() for c in Customer.objects.filter(owner=request.user)]

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            sub_total = float(data.get('sub_total', 0.0))
            amount_payed = float(data.get('amount_payed', 0.0))
            amount_change = float(data.get('amount_change', 0.0))
            dp_val = amount_payed if amount_payed < sub_total else 0.0

            if sub_total <= 0 or not data.get('products'):
                return JsonResponse({
                    'success': False, 
                    'message': 'Penjualan tidak valid (Total nol atau tanpa produk).'
                }, status=400)

            # Gunakan transaction.atomic untuk keamanan konsistensi data database
            with db_transaction.atomic():
                # --- CUSTOMER HANDLING ---
                customer_obj = None
                new_name = data.get('new_customer_name', '').strip()
                new_address = data.get('new_customer_address', '').strip()
                new_phone = data.get('new_customer_phone', '').strip()

                if new_name:
                    customer_obj, created = Customer.objects.get_or_create(
                        first_name__iexact=new_name,
                        owner=request.user,
                        defaults={
                            'first_name': new_name,
                            'address': new_address,
                            'phone': new_phone,
                            'owner': request.user
                        }
                    )
                else:
                    customer_id = data.get('customer')
                    if customer_id:
                        customer_obj = Customer.objects.get(id=int(customer_id), owner=request.user)
                # --- TRANSAKSI UTAMA ---
                new_sale = Sale.objects.create(
                    customer=customer_obj,
                    sub_total=sub_total,
                    amount_payed=amount_payed,
                    amount_change=amount_change,
                    dp_amount=dp_val,
                    owner=request.user
                )
                # --- SALE DETAIL & PRODUCT HANDLING (SINGLE LOOP) ---
                for i, product in enumerate(data['products']):
                    
                    # 1. Cleaning & Validasi Harga
                    price_value = product.get('price')
                    if price_value in [None, '']:
                        price_float = 0.0
                    else:
                        price_float = float(price_value)

                    product_obj = None
                    
                    # 2. Ambil / Buat Produk
                    if not product.get('id'):  # Produk Baru
                        product_name = product.get('name', '').strip()
                        if not product_name:
                            raise ValueError("Nama produk baru tidak boleh kosong.")
                        
                        existing_product = Product.objects.filter(
                            name__iexact=product_name, 
                            owner=request.user
                        ).first()

                        if existing_product:
                            product_obj = existing_product
                        else:
                            try:
                                default_category = Category.objects.get(name='Uncategorized', owner=request.user)
                            except Category.DoesNotExist:
                                default_category, _ = Category.objects.get_or_create(
                                    name='Uncategorized', 
                                    owner=request.user,
                                    defaults={'owner': request.user}
                                )
                            
                            product_obj = Product.objects.create(
                                name=product_name,
                                price=price_float,
                                owner=request.user,
                                description='Deskripsi Produk Baru',
                                status='ACTIVE',
                                category=default_category
                            )
                    else:  # Produk Eksisting
                        try:
                            product_obj = Product.objects.get(
                                id=int(product['id']), 
                                owner=request.user
                            )
                        except Product.DoesNotExist:
                            raise ValueError(f'Produk dengan ID {product["id"]} tidak ditemukan.')

                    qty = int(product.get('quantity', 1))
                    total_prod = float(product.get('total_product', 0.0))

                    # 3. Buat SaleDetail
                    SaleDetail.objects.create(
                        sale=new_sale,
                        product=product_obj,
                        price=price_float,
                        quantity=qty,
                        total_detail=total_prod
                    )

                    # 4. Update Stok
                    stock_obj, _ = Stock.objects.get_or_create(
                        product=product_obj,
                        defaults={"quantity": 0}
                    )
                    stock_obj.quantity = F("quantity") - qty
                    stock_obj.save()

            # Response sukses jika blok atomic selesai tanpa error
            return JsonResponse({
                'success': True,
                'message': f'Transaksi #{new_sale.id} berhasil dibuat!',
                'redirect_url': '/sales/' 
            })

        except Product.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Terjadi kesalahan: Salah satu produk tidak ditemukan.'
            }, status=404)
            
        except Customer.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Terjadi kesalahan: Customer tidak ditemukan.'
            }, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'message': 'Format data JSON tidak valid.'
            }, status=400)

        except ValueError as e:
            return JsonResponse({
                'success': False, 
                'message': f'Validasi Data Gagal: {str(e)}'
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Terjadi kesalahan server: {str(e)}'
            }, status=500)

    # --- HANDLING GET REQUEST ---
    ocr_data = request.session.pop("ocr_result", None)
    ocr_data_json = None
    if ocr_data:
        try:
            ocr_data_json = json.dumps(ocr_data)
        except Exception as e:
            print("Error dumping OCR data JSON:", e)

    context = {
        "breadcrumb": {"parent": "POS", "child": "Point Of Sale"},
        "active_icon": "sales",
        "customers": customers,
        "ocr_data": ocr_data,
        "ocr_data_json": ocr_data_json,
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
        # Kembalikan stok (dikurangi kembali)
        details = SaleDetail.objects.filter(sale=sale)
        for detail in details:
            try:
                stock_obj = Stock.objects.get(product=detail.product)
                stock_obj.quantity = F("quantity") - detail.quantity
                stock_obj.save()
            except Stock.DoesNotExist:
                pass

        details.delete()
        sale.delete()

        messages.success(request, "Transaksi penjualan berhasil dihapus dan stok penyesuaian telah dikembalikan!")
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
    def get(self, request, sale_id, *args, **kwargs):
        sale = get_object_or_404(Sale, id=sale_id, owner=request.user)
        details = SaleDetail.objects.filter(sale=sale)

        data = {
            "sale": sale,
            "details": details
        }

        pdf_response = render_to_pdf('sales/sales_receipt_pdf.html', data)
        if pdf_response:
            pdf_response['Content-Disposition'] = 'inline'
            return pdf_response
        return HttpResponse("Gagal membuat PDF nota.", status=500)
