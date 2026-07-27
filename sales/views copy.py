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
from products.models import Category
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
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

from .forms import ReceiptUploadForm
from .services.ocr import read_receipt
from .services.parser import parse_receipt


from sales.services.ocr_services import process_receipt


def upload_receipt(request):
    if request.method != "POST":
        return redirect("sales:sales_list")

    image = request.FILES.get("file_transaksi")

    if not image:
        return redirect("sales:sales_list")

    request.session["ocr_result"] = process_receipt(image)

    return redirect("sales:preview_receipt")
def preview_receipt(request):
    return render(
        request,
        "sales/preview_receipt.html",
        {"data": request.session.get("ocr_result")},
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
    )

    context = {
        "breadcrumb": {"parent": "POS", "child": "Point Of Sale"},
        "active_icon": "sales",
        "sales": Sale.objects.filter(owner=request.user).order_by('-id'),
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
            print("--- LOG 1: Data AJAX Diterima ---") 
            print(data) # Cetak semua data yang diterima
            
            # --- CUSTOMER HANDLING (tetap sama) ---
            customer_obj = None
            new_name = data.get('new_customer_name', '').strip()
            new_address = data.get('new_customer_address', '').strip()
            new_phone = data.get('new_customer_phone', '').strip()
            if new_name:
                print("--- LOG 2: Mencoba Membuat/Mendapatkan Customer Baru ---")
                customer_obj, created = Customer.objects.get_or_create(
                    first_name__iexact=new_name,
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
                    customer_obj = Customer.objects.get(id=int(customer_id),owner=request.user)

            print("--- LOG 3: Customer Selesai Dikonfigurasi ---")
            # --- TRANSAKSI UTAMA (tetap sama) ---
            sub_total = float(data.get('sub_total', 0.0))
            amount_payed = float(data.get('amount_payed', 0.0))
            amount_change = float(data.get('amount_change', 0.0))

            if sub_total <= 0 or not data.get('products'):
                 return JsonResponse({'success': False, 'message': 'Penjualan tidak valid (Total nol atau tanpa produk).'}, status=400)

            new_sale = Sale.objects.create(
                customer=customer_obj,
                sub_total=sub_total,
                amount_payed=amount_payed,
                amount_change=amount_change,
                owner=request.user
            )
            
            print(f"--- LOG 4: Sale ID {new_sale.id} Dibuat ---")

            # --- SALE DETAIL & PRODUCT HANDLING ---
            for i, product in enumerate(data['products']):
                product_obj = None

                # AMBIL NILAI HARGA DAN BERSIHKAN DAHULU
                price_value = product.get('price')
                if price_value in [None, '']:
                    price_float = 0.0
                else:
                    try:
                        price_float = float(price_value)
                    except (TypeError, ValueError):
                        price_float = 0.0

                # Log setiap produk yang diproses
                print(f"--- LOG 5: Memproses Produk ke-{i} ---")

                # Tangani produk baru atau lama
                if not product.get('id'):  # Produk Baru
                    product_name = product.get('name', '').strip()
                    if not product_name:
                        raise ValueError("Nama produk baru tidak boleh kosong.")
                    print(f"--- LOG 6: Mencoba Membuat Produk BARU: {product_name} ---")
                    try:
                        default_category = Category.objects.get(name='Uncategorized', owner=request.user)
                    except Category.DoesNotExist:
                        default_category, created = Category.objects.get_or_create(
                            name='Uncategorized', defaults={'owner': request.user}
                        )
                    new_product = Product.objects.create(
                        name=product_name,
                        price=price_float,
                        owner=request.user,
                        description='Deskripsi Produk Baru',
                        status='ACTIVE',
                        category=default_category
                    )
                    product_obj = new_product
                else:  # Produk Lama
                    try:
                        product_obj = Product.objects.get(
                            id=int(product['id']),
                            owner=request.user
                        )
                    except Product.DoesNotExist:
                        return JsonResponse({'success': False, 'message': f'Produk dengan ID {product["id"]} tidak ditemukan atau tidak memiliki izin.'}, status=404)

                # Buat atau simpan SaleDetail (gunakan nilai default jika tidak tersedia)
                quantity = product.get('quantity', 1)
                try:
                    quantity = int(quantity)
                except (TypeError, ValueError):
                    quantity = 1

                total_product = product.get('total_product', 0.0)
                try:
                    total_product = float(total_product)
                except (TypeError, ValueError):
                    total_product = round(quantity * price_float, 2)

                SaleDetail.objects.create(
                    sale=new_sale,
                    product=product_obj,
                    price=price_float,
                    quantity=quantity,
                    total_detail=total_product
                )
            print("--- LOG 7: Semua Produk Diproses. Berhasil! ---")
                
            # 3. Respon Sukses
            response_data = {
                'success': True,
                'message': f'Transaksi #{new_sale.id} berhasil dibuat!',
                'redirect_url': '/sales/' 
            }
            return JsonResponse(response_data)

        except Product.DoesNotExist:
            response_data = {'success': False, 'message': 'Terjadi kesalahan: Salah satu produk tidak ditemukan.'}
            return JsonResponse(response_data, status=404)
            
        except Customer.DoesNotExist:
            response_data = {'success': False, 'message': 'Terjadi kesalahan: Customer tidak ditemukan.'}
            return JsonResponse(response_data, status=404)
            
        except json.JSONDecodeError:
            response_data = {'success': False, 'message': 'Format data JSON tidak valid.'}
            return JsonResponse(response_data, status=400)

        except ValueError as e:
            # Ini akan menangkap "could not convert string to float: ''"
            response_data = {'success': False, 'message': f'Validasi Data Gagal: Pastikan semua nilai numerik terisi dengan benar. Detail: {str(e)}'}
            return JsonResponse(response_data, status=400)

        except Exception as e:
            response_data = {
                'success': False,
                'message': f'Terjadi kesalahan server: {str(e)}'
            }
            return JsonResponse(response_data, status=500)
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
