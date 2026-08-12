from django.contrib.auth.models import User
from django.db import transaction
import json
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa
import sweetify

from products.models import Product, Category
from zetaapp.models import Stock
from .models import Purchase, PurchaseDetail


@login_required(login_url="/accounts/login/")
def purchase_list_view(request):
    purchases = Purchase.objects.filter(owner=request.user).order_by('-id')

    totals = purchases.aggregate(
        total_transactions=Count('id'),
        total_items=Sum('purchasedetail__quantity'),
        total_expense=Sum('sub_total'),
    )

    context = {
        "breadcrumb": {"parent": "Transaksi", "child": "Pembelian (Barang Masuk)"},
        "active_icon": "purchases",
        "purchases": purchases,
        "totals": totals,
    }
    return render(request, "purchases/purchases.html", context=context)


# Helper function untuk membersihkan input angka
def clean_num(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Hapus karakter selain angka, titik, dan minus
    val_str = str(value).replace("Rp", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0


def get_user_instance(user_input):
    if isinstance(user_input, User):
        return user_input
    if hasattr(user_input, 'pk'):
        try:
            return User.objects.get(pk=user_input.pk)
        except Exception:
            pass
    try:
        return User.objects.get(pk=int(user_input))
    except Exception:
        return User.objects.first()


@login_required(login_url="/accounts/login/")
def purchase_add_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            current_user = get_user_instance(request.user)

            data = json.loads(request.body)
            supplier_name = data.get('supplier_name', '').strip() or 'Umum'
            note = data.get('note', '').strip()

            sub_total = clean_num(data.get('sub_total', 0.0))
            ongkos_muat = clean_num(data.get('ongkos_muat', 0.0))
            gaji_pegawai = clean_num(data.get('gaji_pegawai', 0.0))
            biaya_lain = clean_num(data.get('biaya_lain', 0.0))
            susutan_persen = clean_num(data.get('susutan_persen', 0.0))
            tabungan_persen = clean_num(data.get('tabungan_persen', 30.0))

            if sub_total <= 0 or not data.get('products'):
                return JsonResponse({
                    'success': False, 
                    'message': 'Transaksi tidak valid (Total nol atau tanpa produk).'
                }, status=400)

            from zetaapp.models import Profito2

            with transaction.atomic():
                # Pre-process products to get buy prices and calculate totals
                processed_items = []
                total_qty = 0.0
                total_modal = 0.0

                for product in data['products']:
                    price_float = clean_num(product.get('price')) # Selling price per kg/unit
                    qty_float = clean_num(product.get('quantity'))
                    if qty_float <= 0:
                        qty_float = 1.0

                    total_det = clean_num(product.get('total_product'))
                    if total_det <= 0:
                        total_det = price_float * qty_float

                    product_id = product.get('id')
                    if not product_id or str(product_id).lower() in ['null', 'none', '']:
                        product_name = product.get('name', '').strip()
                        if not product_name:
                            raise ValueError("Nama produk baru tidak boleh kosong.")

                        existing_product = Product.objects.filter(
                            name__iexact=product_name
                        ).first()

                        if existing_product:
                            product_obj = existing_product
                        else:
                            default_category, _ = Category.objects.get_or_create(
                                name='Uncategorized', 
                                defaults={'owner': current_user}
                            )
                            product_obj = Product.objects.create(
                                name=product_name,
                                price=price_float,
                                owner=current_user,
                                description='Deskripsi Produk Baru',
                                status='ACTIVE',
                                category=default_category
                            )
                    else:
                        try:
                            product_obj = Product.objects.get(
                                id=int(product_id)
                            )
                        except (Product.DoesNotExist, ValueError):
                            raise ValueError(f'Produk dengan ID {product_id} tidak ditemukan.')

                    avg_buy_price = clean_num(product.get('avg_buy_price')) or float(product_obj.price or 0.0)
                    total_modal += avg_buy_price * qty_float
                    total_qty += qty_float

                    processed_items.append({
                        'product_obj': product_obj,
                        'price_float': price_float,
                        'qty_float': qty_float,
                        'total_det': total_det,
                        'avg_buy_price': avg_buy_price,
                    })

                profit_kotor = sub_total - total_modal
                susutan_val = sub_total * (susutan_persen / 100.0)
                total_biaya_op = ongkos_muat + gaji_pegawai + biaya_lain + susutan_val
                net_profit = profit_kotor - total_biaya_op
                tabungan_amount = max(0.0, net_profit) * (tabungan_persen / 100.0)

                new_purchase = Purchase.objects.create(
                    supplier_name=supplier_name,
                    note=note,
                    sub_total=sub_total,
                    grand_total=sub_total,
                    owner=current_user,
                    ongkos_muat=ongkos_muat,
                    gaji_pegawai=gaji_pegawai,
                    biaya_lain=biaya_lain,
                    susutan_persen=susutan_persen,
                    tabungan_persen=tabungan_persen,
                    profit_kotor=profit_kotor,
                    net_profit=net_profit,
                    tabungan_amount=tabungan_amount
                )

                for item in processed_items:
                    product_obj = item['product_obj']
                    price_float = item['price_float']
                    qty_float = item['qty_float']
                    total_det = item['total_det']
                    avg_buy_price = item['avg_buy_price']

                    PurchaseDetail.objects.create(
                        purchase=new_purchase,
                        product=product_obj,
                        cost_price=price_float,
                        quantity=qty_float,
                        total_detail=total_det
                    )

                    # UPDATE STOK OTOMATIS: Barang Keluar (Jual) -> Stok BERKURANG
                    stock_obj, _ = Stock.objects.get_or_create(
                        product=product_obj,
                        defaults={"quantity": 0.0}
                    )
                    stock_obj.quantity = float(stock_obj.quantity) - qty_float
                    stock_obj.save()

                    # SYNC KE PROFIT MODULE (Profito2)
                    portion = (qty_float / total_qty) if total_qty > 0 else (1.0 / len(processed_items))
                    item_ongkos_muat = (ongkos_muat * portion) / qty_float if qty_float > 0 else 0
                    item_gaji_pegawai = (gaji_pegawai * portion) / qty_float if qty_float > 0 else 0
                    item_biaya_lain = (biaya_lain * portion) / qty_float if qty_float > 0 else 0

                    Profito2.objects.create(
                        nama_barang=product_obj.name,
                        berat_input=qty_float,
                        harga_beli_per_kg=avg_buy_price,
                        harga_jual_per_kg=price_float,
                        solar=item_biaya_lain,
                        karung=0,
                        ongkos_kirim=0,
                        ongkos_sortir=0,
                        ongkos_giling=0,
                        ongkos_muat=item_ongkos_muat,
                        gaji_pegawai=item_gaji_pegawai,
                        susutan_persen=susutan_persen,
                        tabungan_persen=tabungan_persen,
                        keterangan=f"Otomatis dari Barang Keluar (Jual) #{new_purchase.transaction_number} (Pabrik: {supplier_name})",
                        purchase=new_purchase
                    )

            return JsonResponse({
                'success': True,
                'message': f'Transaksi Barang Keluar #{new_purchase.transaction_number} berhasil disimpan dan dicatat ke Profit!',
                'redirect_url': '/purchases/'
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Format data JSON tidak valid.'}, status=400)

        except ValueError as e:
            return JsonResponse({'success': False, 'message': f'Validasi Data Gagal: {str(e)}'}, status=400)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Terjadi kesalahan server: {str(e)}'}, status=500)

    context = {
        "breadcrumb": {"parent": "Transaksi", "child": "Tambah Barang Keluar (Jual)"},
        "active_icon": "purchases",
    }
    return render(request, "purchases/purchases_add.html", context=context)

@login_required(login_url="/accounts/login/")
def purchase_details_view(request, purchase_id):
    try:
        purchase = Purchase.objects.get(id=purchase_id, owner=request.user)
        details = PurchaseDetail.objects.filter(purchase=purchase)

        context = {
            "breadcrumb": {"parent": "Transaksi", "child": "Detail Barang Keluar (Jual)"},
            "active_icon": "purchases",
            "purchase": purchase,
            "details": details,
        }
        return render(request, "purchases/purchases_details.html", context=context)
    except Exception as e:
        messages.error(request, 'Terjadi kesalahan saat mengambil data.')
        return redirect('purchases:purchase_list')


@login_required(login_url="/accounts/login/")
def delete_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, owner=request.user)

    if request.method == "POST":
        # Kembalikan stok (ditambah kembali)
        details = PurchaseDetail.objects.filter(purchase=purchase)
        for detail in details:
            try:
                stock_obj = Stock.objects.get(product=detail.product)
                stock_obj.quantity = F("quantity") + detail.quantity
                stock_obj.save()
            except Stock.DoesNotExist:
                pass

        details.delete()
        purchase.delete()

        messages.success(request, "Transaksi berhasil dihapus dan stok telah dikembalikan!")
        return redirect('purchases:purchase_list')

    messages.error(request, "Permintaan tidak valid.")
    return redirect('purchases:purchase_list')


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


class ViewPDF(View):
    def get(self, request, purchase_id, *args, **kwargs):
        purchase = get_object_or_404(Purchase, id=purchase_id, owner=request.user)
        details = PurchaseDetail.objects.filter(purchase=purchase)

        data = {
            "purchase": purchase,
            "details": details
        }

        pdf = render_to_pdf('purchases/purchases_receipt_pdf.html', data)
        return HttpResponse(pdf, content_type='application/pdf')
