from babel import localedata
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
import openpyxl
from datetime import datetime, date, time, timedelta
from django.db import transaction
import re
import os
from decimal import Decimal, InvalidOperation
from .helpers import *
from collections import defaultdict
from .models import *
from .forms import *
from django.contrib import messages
import locale
from babel.numbers import format_currency
from django.db.models import Q, Sum, F, Value, DecimalField, ExpressionWrapper
from django.template.loader import get_template
from io import BytesIO
from django.views.decorators.http import require_POST, require_GET
from xhtml2pdf import pisa
from django.views import View
from django.db.models.functions import ExtractMonth, ExtractYear, TruncDate, TruncMonth, Coalesce
from django.utils import timezone
import pandas as pd
import calendar, json, logging
from django.forms import modelformset_factory, formset_factory
from .models import StockIn, Product
from .forms import ExcelUploadForm, StockInForm
from sales.models import Sale, SaleDetail
from .models import Transaksi
@login_required(login_url="/accounts/login/")
def transaksi_history(request):
    status_filter = request.GET.get('status', 'ALL').upper()
    data = Sale.objects.filter(owner=request.user).order_by('-id')

    if status_filter == 'LUNAS':
        data = data.filter(Q(amount_payed__gte=F('sub_total')) | Q(afkiran__status='LUNAS'))
    elif status_filter == 'BELUM_LUNAS':
        data = data.filter(Q(amount_payed__lt=F('sub_total')) | Q(afkiran__status='PENDING'))

    # Menghitung ringkasan statistik untuk Hari Ini
    today = timezone.localtime(timezone.now()).date()
    sales_today = Sale.objects.filter(owner=request.user)
    
    total_transactions = sales_today.count()
    total_revenue = sales_today.aggregate(total=Sum('sub_total'))['total'] or 0
    total_items = SaleDetail.objects.filter(sale__in=sales_today).aggregate(total=Sum('quantity'))['total'] or 0
    average_transaction = total_revenue / total_transactions if total_transactions > 0 else 0

    context = {
        'data': data,
        'status_filter': status_filter,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'average_transaction': average_transaction,
        "breadcrumb": {"parent": "Laporan", "child": "Histori Transaksi"},
    }
    return render(request, 'transaksi/transaksi_history.html', context)


@require_GET
def product_search_api(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        products = Product.objects.filter(name__icontains=q)[:20] | Product.objects.filter(sku__icontains=q)[:20]
        for p in products:
            results.append({'id': p.id, 'text': f'{p.sku} — {p.name}'})
    return JsonResponse({'results': results})
@login_required
def stockin_create(request):
    """
    Menampilkan halaman untuk menambah banyak StockIn sekaligus menggunakan modelformset.
    """
    products = Product.objects.filter(owner=request.user).order_by('name')
    errors = []

    if request.method == 'POST':
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        references = request.POST.getlist('reference[]')
        notes = request.POST.getlist('note[]')

        for idx, (p_id, qty, ref, note) in enumerate(zip(product_ids, quantities, references, notes), start=1):
            if not p_id or not qty:
                errors.append(f"Baris {idx}: Produk dan jumlah harus diisi.")
                continue
            try:
                product = Product.objects.get(id=p_id)
                StockIn.objects.create(
                    product=product,
                    quantity=qty,
                    reference=ref,
                    note=note
                )
            except Product.DoesNotExist:
                errors.append(f"Baris {idx}: Produk tidak ditemukan.")

        if not errors:
            return redirect('stockin_list')

    return render(request, 'stok/stockin_form.html', {'products': products, 'errors': errors})


@login_required
def stockin_list(request):
    from purchases.models import PurchaseDetail

    user_products = Product.objects.filter(owner=request.user, status='ACTIVE')

    stock_data = []
    for product in user_products:
        total_masuk = SaleDetail.objects.filter(
            product=product, sale__owner=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_keluar = PurchaseDetail.objects.filter(
            product=product, purchase__owner=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0

        stok = float(total_masuk) - float(total_keluar)
        if total_masuk > 0 or total_keluar > 0 or stok > 0:
            display_stok = max(0.0, stok)
            sell_price = float(product.selling_price) if product.selling_price else float(product.price)
            stock_data.append({
                'product': product,
                'total_masuk': float(total_masuk),
                'total_keluar': float(total_keluar),
                'stok': display_stok,
                'selling_price': sell_price,
                'nilai_estimasi': display_stok * sell_price,
            })

    # Sort by stok descending, then total_masuk descending
    stock_data.sort(key=lambda x: (x['stok'], x['total_masuk']), reverse=True)

    # KPI
    total_jenis = len(stock_data)
    total_stok_kg = sum(s['stok'] for s in stock_data)
    total_nilai = sum(s['nilai_estimasi'] for s in stock_data)

    context = {
        'stock_data': stock_data,
        'total_jenis': total_jenis,
        'total_stok_kg': total_stok_kg,
        'total_nilai': total_nilai,
        'breadcrumb': {'parent': 'Stok Barang', 'child': 'Stok Gudang'},
    }
    return render(request, "stok/stockin_list.html", context)

@login_required
def stockin_delete(request, pk):
    si = get_object_or_404(StockIn, pk=pk)
    if request.method == "POST":
        si.delete()
        messages.success(request, "Data barang masuk berhasil dihapus.")
        return redirect("stockin_list")
    return redirect("stockin_list")

def stockin_update(request, pk):
    si = get_object_or_404(StockIn, pk=pk)
    if request.method == "POST":
        form = StockInForm(request.POST, instance=si)
        if form.is_valid():
            form.save()
            messages.success(request, "Data barang masuk berhasil diperbarui.")
        else:
            messages.error(request, "Gagal memperbarui data.")
    return redirect("stockin_list")


@login_required
def get_product_summary(request):
    data = (
        SaleDetail.objects
        .filter(sale__owner=request.user)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:10]
    )
    top = list(data[:10])
    others = data[10:]

    others_total = sum(item['total_qty'] for item in others)

    if others_total > 0:
        top.append({
            'product__name': 'Lainnya',
            'total_qty': others_total
        })
    product_names = [d['product__name'] for d in data]
    product_totals = [float(d['total_qty']) for d in data]

    return JsonResponse({
        'product_names': product_names,
        'product_totals': product_totals
    })

@login_required
def product_analysis(request):

    products = (
        SaleDetail.objects
        .filter(sale__owner=request.user)
        .values('product__id', 'product__name')
        .annotate(
            total_qty=Sum('quantity'),
            omzet=Sum(
                ExpressionWrapper(
                    F('quantity') * F('price'),
                    output_field=DecimalField()
                )
            )
        )
        .order_by('-total_qty')
    )

    # KPI aggregations
    total_products = products.count()
    total_sold = sum(float(p['total_qty'] or 0) for p in products)
    total_omzet = sum(float(p['omzet'] or 0) for p in products)

    # Top 10 for chart
    top10 = list(products[:10])
    chart_names = json.dumps([p['product__name'] for p in top10])
    chart_qty = json.dumps([float(p['total_qty'] or 0) for p in top10])
    chart_omzet = json.dumps([float(p['omzet'] or 0) for p in top10])

    context = {
        'products': products,
        'total_products': total_products,
        'total_sold': total_sold,
        'total_omzet': total_omzet,
        'chart_names': chart_names,
        'chart_qty': chart_qty,
        'chart_omzet': chart_omzet,
        'breadcrumb': {'parent': 'Dashboard', 'child': 'Analisis Produk'},
    }
    return render(request, 'general/dashboard/default/components/product_analysis.html', context)

def LandingPage(request):
    return render(request, 'landingpage/index.html')
def Tentang(request):
    return render(request, 'landingpage/tentang.html')
def Layanan(request):
    return render(request, 'landingpage/layanan.html')
def Produk(request):
    return render(request, 'landingpage/produk.html')
def Galeri(request):
    return render(request, 'landingpage/galeri.html')
def Kontak(request):
    return render(request, 'landingpage/kontak.html')
    
@login_required(login_url="/accounts/login/")
def indexPage(request):
    user = request.user
    today = timezone.localtime(timezone.now()).date()
    user_transaksi = Transaksi.objects.filter(owner=user)
    data = user_transaksi.order_by('-tanggal')[:5]
    count = user_transaksi.count()
    stats_transaksi = user_transaksi.aggregate(
        pemasukan_harian=Sum('jumlah', filter=Q(tanggal=today, transaksi_choice='P')),
        pengeluaran_harian=Sum('jumlah', filter=Q(tanggal=today, transaksi_choice='L')),
        pemasukan_bulanan=Sum('jumlah', filter=Q(tanggal__year=today.year, tanggal__month=today.month, transaksi_choice='P')),
        pengeluaran_bulanan=Sum('jumlah', filter=Q(tanggal__year=today.year, tanggal__month=today.month, transaksi_choice='L')),
        pemasukan_tahunan=Sum('jumlah', filter=Q(tanggal__year=today.year, transaksi_choice='P')),
        pengeluaran_tahunan=Sum('jumlah', filter=Q(tanggal__year=today.year, transaksi_choice='L')),
    )

    # Ambil nilai agregasi dengan fallback 0 jika None
    total_pemasukan_harian = stats_transaksi['pemasukan_harian'] or 0
    total_pengeluaran_harian = stats_transaksi['pengeluaran_harian'] or 0

    total_pemasukan_bulanan = stats_transaksi['pemasukan_bulanan'] or 0
    total_pengeluaran_bulanan = stats_transaksi['pengeluaran_bulanan'] or 0

    total_pemasukan_tahunan = stats_transaksi['pemasukan_tahunan'] or 0
    total_pengeluaran_tahunan = stats_transaksi['pengeluaran_tahunan'] or 0

    # 3. Agregasi Hutang & Piutang (Tahunan)
    stats_hp = HutangPiutang.objects.filter(
        owner=user, 
        tanggal__year=today.year
    ).aggregate(
        total_hutang=Sum('jumlah', filter=Q(hutang_choice='H')),
        total_piutang=Sum('jumlah', filter=Q(hutang_choice='P'))
    )

    total_hutang = stats_hp['total_hutang'] or 0
    total_piutang = stats_hp['total_piutang'] or 0
    sisa_hutang = total_piutang - total_hutang

    # 4. Penjualan Produk Per Item (Terfilter User via relasi transaksi/sale)
    totals_per_product = (
        SaleDetail.objects
        .filter(sale__owner=user)  # Sesuaikan 'sale__owner' sesuai nama field relation di model Anda
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )
    product_names = [p['product__name'] for p in totals_per_product]
    product_totals = [p['total_qty'] for p in totals_per_product]

    # 5. Kalkulasi Cashflow
    total_pemasukan2 = (Transaksi.objects.filter(owner=request.user,transaksi_choice=Transaksi.PEMASUKAN).aggregate(total=Sum('jumlah'))['total'] or 0)
    total_pengeluaran2 = (Transaksi.objects.filter(owner=request.user,transaksi_choice=Transaksi.PENGELUARAN).aggregate(total=Sum('jumlah'))['total'] or 0)
    saldo = total_pemasukan2 - total_pengeluaran2
    sisa_cashflow_harian = total_pemasukan_harian - total_pengeluaran_harian
    sisa_cashflow_bulanan = total_pemasukan_bulanan - total_pengeluaran_bulanan
    sisa_cashflow_tahunan = total_pemasukan_tahunan - total_pengeluaran_tahunan

    context = {
        "breadcrumb": {"parent": "Dashboard", "child": "Dashboard"},
        'total_pemasukan_harian': total_pemasukan_harian,
        'total_pemasukan2':total_pemasukan2,
        'total_pengeluaran2':total_pengeluaran2,
        'total_pemasukan_bulanan': total_pemasukan_bulanan,
        'total_pemasukan_tahunan': total_pemasukan_tahunan,
        'total_pengeluaran_harian': total_pengeluaran_harian,
        'total_pengeluaran_bulanan': total_pengeluaran_bulanan,
        'total_pengeluaran_tahunan': total_pengeluaran_tahunan,
        'sisa_cashflow_harian': sisa_cashflow_harian,
        'sisa_cashflow_bulanan': sisa_cashflow_bulanan,
        'sisa_cashflow_tahunan': sisa_cashflow_tahunan,
        'total_hutang': total_hutang,
        'total_piutang': total_piutang,
        'sisa_hutang': sisa_hutang,
        'saldo': saldo,
        'data': data,
        'count': count,
        'product_names': product_names,
        'product_totals': product_totals,
    }

    return render(request, 'general/dashboard/default/index.html', context)
#PROFIT
# @login_required(login_url="/accounts/login/")
# def profit_create(request):
#     if request.method == 'POST':
#         form = ProfitForms(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Formulir Berhasil Dibuat")
#             return redirect('profit')  # ganti sesuai nama url list
#     else:
#         form = ProfitForms()
    
#     return render(request, 'profit/tambah_profit.html', {'form': form})

@login_required(login_url="/accounts/login/")
def profit_create(request): # Nama view baru
    if request.method == 'POST':
        # 1. Inisialisasi kedua form dengan data POST
        formset = ItemFormSet(request.POST, prefix='item') # Gunakan prefix
        global_form = GlobalCostForm(request.POST, prefix='global') # Gunakan prefix

        # 2. Validasi kedua form
        if formset.is_valid() and global_form.is_valid():
            
            # Ambil data global yang sudah divalidasi
            global_data = global_form.cleaned_data
            
            # Simpan formset dengan commit=False
            instances = formset.save(commit=False)
            
            for instance in instances:
                # 3. Masukkan data global ke setiap instance Formset
                instance.solar = global_data['solar']
                instance.karung = global_data['karung']
                instance.ongkos_kirim = global_data['ongkos_kirim']
                instance.ongkos_sortir = global_data['ongkos_sortir']
                instance.ongkos_giling = global_data['ongkos_giling']
                instance.ongkos_muat = global_data['ongkos_muat']
                instance.susutan_persen = global_data['susutan_persen']
                instance.tabungan_persen = global_data['tabungan_persen']
                
                # Setelah semua field terisi, panggil save() yang akan menjalankan perhitungan otomatis
                instance.save()
            
            # Hapus objek yang ditandai untuk dihapus (jika ada)
            for obj in formset.deleted_objects:
                obj.delete()    
                
            messages.success(request, "Semua data profit berhasil disimpan.")
            return redirect('profit') # Ganti sesuai URL list profit Anda
        
        else:
            messages.error(request, "Terdapat kesalahan input. Mohon periksa kembali formulir.")
    
    else:
        # Tampilkan form saat GET request
        formset = ItemFormSet(queryset=Profito2.objects.none(), prefix='item')
        # Tampilkan biaya global dengan nilai default dari model
        global_form = GlobalCostForm(prefix='global')
    
    context = {
        'formset': formset,
        'global_form': global_form,
        "breadcrumb": {"parent": "Profit", "child": "Input Multiple"},
    }
    return render(request, 'profit/tambah_profit.html', context)
@login_required(login_url="/accounts/login/")
def profit(request):
    from purchases.models import PurchaseDetail, Purchase
    from decimal import Decimal
    data = Profito2.objects.all().select_related('purchase').order_by('-tanggal')
    profit_today = profit_today_value()
    formatted = format_currency(profit_today, 'IDR', locale='id_ID')
    datenow = timezone.now().strftime("%d-%m-%Y")

    # KPI Aggregate dari Profito2
    agg = data.aggregate(
        total_profit_kotor=Sum('total_revenue'),
        total_hpp=Sum('total_hpp'),
        total_profit_bersih=Sum('profit'),
        total_tabungan=Sum('tabungan_total'),
    )
    total_revenue_all = float(agg.get('total_profit_kotor') or 0)
    total_hpp_all = float(agg.get('total_hpp') or 0)
    total_profit_kotor = total_revenue_all - total_hpp_all
    total_net_profit = float(agg.get('total_profit_bersih') or 0)
    total_tabungan = float(agg.get('total_tabungan') or 0)
    total_biaya_op = total_profit_kotor - total_net_profit  # selisih gross vs net

    # KPI dari Purchases untuk biaya operasional yang dicatat di Purchase
    purch_agg = Purchase.objects.filter(owner=request.user).aggregate(
        sum_ongkos_muat=Sum('ongkos_muat'),
        sum_gaji_pegawai=Sum('gaji_pegawai'),
        sum_biaya_lain=Sum('biaya_lain'),
        sum_net_profit=Sum('net_profit'),
        sum_tabungan=Sum('tabungan_amount'),
    )
    purch_ongkos_muat = float(purch_agg.get('sum_ongkos_muat') or 0)
    purch_gaji_pegawai = float(purch_agg.get('sum_gaji_pegawai') or 0)
    purch_biaya_lain = float(purch_agg.get('sum_biaya_lain') or 0)
    purch_net_profit = float(purch_agg.get('sum_net_profit') or 0)
    purch_tabungan = float(purch_agg.get('sum_tabungan') or 0)

    # Hitung Estimasi Profit Margin Stok POS (Optimized: 2 queries instead of 2N queries)
    user_products = Product.objects.filter(owner=request.user, status='ACTIVE')
    sales_map = dict(
        SaleDetail.objects.filter(sale__owner=request.user, product__in=user_products)
        .values('product_id')
        .annotate(total=Sum('quantity'))
        .values_list('product_id', 'total')
    )
    purchases_map = dict(
        PurchaseDetail.objects.filter(purchase__owner=request.user, product__in=user_products)
        .values('product_id')
        .annotate(total=Sum('quantity'))
        .values_list('product_id', 'total')
    )

    pos_estimated_stock_profit = 0.0
    for product in user_products:
        total_masuk = float(sales_map.get(product.id, 0) or 0)
        total_keluar = float(purchases_map.get(product.id, 0) or 0)

        stok = total_masuk - total_keluar
        if stok > 0:
            sell_price = float(product.selling_price) if product.selling_price else float(product.price)
            buy_price = float(product.price)
            margin = max(0.0, sell_price - buy_price)
            pos_estimated_stock_profit += stok * margin

    # Hitung Realized POS Sales Profit Hari Ini (Optimized with select_related)
    today = timezone.localtime(timezone.now()).date()
    sales_today_details = SaleDetail.objects.filter(
        sale__owner=request.user,
        sale__date_added__date=today
    ).select_related('product')
    pos_profit_today = 0.0
    for detail in sales_today_details:
        buy_p = float(detail.product.price) if detail.product else 0.0
        sell_p = float(detail.price)
        pos_profit_today += (sell_p - buy_p) * float(detail.quantity)

    context = {
        'data': data,
        'datenow': datenow,
        'profit_today': formatted[:-3],
        'pos_estimated_stock_profit': pos_estimated_stock_profit,
        'pos_profit_today': pos_profit_today,
        # KPI Profito2
        'total_net_profit': total_net_profit,
        'total_tabungan': total_tabungan,
        'total_profit_kotor': total_profit_kotor,
        'total_biaya_op': total_biaya_op,
        # KPI Purchases
        'purch_ongkos_muat': purch_ongkos_muat,
        'purch_gaji_pegawai': purch_gaji_pegawai,
        'purch_biaya_lain': purch_biaya_lain,
        'purch_net_profit': purch_net_profit,
        'purch_tabungan': purch_tabungan,
        "breadcrumb": {"parent": "Profit", "child": "Analisis Profit"},
    }
    return render(request, 'profit/profit.html', context)

def UpdatePr(request, pk):
    data = get_object_or_404(Profito2, pk=pk)

    if request.method == 'POST':
        form = ProfitForms(request.POST, instance=data)
        if form.is_valid():
            # Simpan sementara untuk memanipulasi sebelum commit
            obj = form.save(commit=False)
            obj.user = request.user  # jika ada relasi user

            # Ambil nilai dari cleaned_data dengan fallback aman
            jumlah_brg = form.cleaned_data.get('jumlah_brg') or 0
            harga_jual = form.cleaned_data.get('harga_jual') or 0
            harga_beli = form.cleaned_data.get('harga_beli') or 0

            # Konversi ke tipe yang sesuai (safely)
            try:
                jumlah = int(jumlah_brg)
            except (TypeError, ValueError):
                jumlah = 0

            try:
                hj = Decimal(str(harga_jual))
            except (InvalidOperation, TypeError):
                hj = Decimal('0')

            try:
                hb = Decimal(str(harga_beli))
            except (InvalidOperation, TypeError):
                hb = Decimal('0')

            # Hitung profit per unit dan total profit
            profit_unit = hj - hb
            total_profit = profit_unit * jumlah

            # Simpan ke field model (pastikan field ini ada di model)
            # Ganti nama field jika model Anda memakai nama lain, mis. 'profit' atau 'profit_total'
            obj.profit_unit = profit_unit
            obj.total_profit = total_profit

            obj.save()

            messages.success(request, "Data profit berhasil diperbarui.")
            return redirect('profit')  # gunakan nama url pattern jika ada
        else:
            # debugging: tampilkan error form ke console / messages
            print(form.errors)
            messages.error(request, 'Formulir tidak valid.')
            messages.error(request, form.errors)
    else:
        # GET: tampilkan form dengan data instance
        form = ProfitForms(instance=data)

    context = {
        'form': form,
        "breadcrumb": {"parent": "profit", "child": "Profit"},
    }
    return render(request, 'profit/edit_profit.html', context)
def DeleteProf(request, pk):
    Profito2.objects.get(id=pk).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/profit/')

def ViewProf(request, pk):
    data = get_object_or_404(Profito2, id=pk)
    return render(request, 'profit/view_profit.html', {"data":data})

@login_required(login_url="/accounts/login/")
def profit_mark_tabung(request, pk):
    profit = get_object_or_404(Profito2, pk=pk)
    if profit.profit_saved != True:
        # Update status profit
        profit.profit_saved = True
        profit.save()

        # Tambahkan ke tabungan
        Tabungan.objects.create(
            nominal=profit.tabungan_total,
            description=f"Tabungan dari profit: {profit.id}",
            date=timezone.now(),
        )
        messages.success(request, "Profit berhasil ditandai sebagai sudah di tabung dan dana masuk ke tabungan.")
    else:
        messages.info(request, "Profit sudah pernah ditabung sebelumnya.")

    return redirect('profit')

#HUTANG ORTU
@login_required(login_url="/accounts/login/")
def hutang(request):
    data = HutangPiutang.objects.filter(owner=request.user).order_by('-tanggal')
    if request.POST :
        excel = ExcelUploadForm(request.POST, request.FILES)
        if excel.is_valid():
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                messages.error(request, 'File bukan berformat Excel (.xlsx)')
                return render(request, 'transaksi/index.html', {'excel': excel})

            df = pd.read_excel(excel_file, engine='openpyxl')

            for index, row in df.iterrows():
                try:
                    tanggal = pd.to_datetime(row['tanggal'], format='%Y-%m-%d')
                except ValueError:
                    messages.warning(request, f"Format tanggal tidak valid pada baris {index + 2}. Baris diabaikan.")
                    continue
                keterangan = row['keterangan']
                pemasukan = row['pemasukan']
                pengeluaran = row['pengeluaran']
                if pd.isna(pemasukan):
                    pemasukan = 0
                if pd.isna(pengeluaran):
                    pengeluaran = 0
                # Menentukan jenis transaksi berdasarkan pemasukan atau pengeluaran
                if pemasukan:
                    hutang_choice = HutangPiutang.PIUTANG
                    jumlah = pemasukan
                elif pengeluaran:
                    hutang_choice = HutangPiutang.HUTANG
                    jumlah = pengeluaran
                else:
                    messages.warning(request, 'Kolom pemasukan atau pengeluaran harus diisi')
                    continue

                # Memeriksa kategori
            
                HutangPiutang.objects.create(
                    tanggal=tanggal,
                    keterangan=keterangan,
                    hutang_choice=hutang_choice,
                    jumlah=jumlah,
                )
        form = HutangForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.owner = request.user
            trform.save()
            messages.success(request, "Formulir Berhasil Dibuat")
            return redirect('/hutang/')
        else:
            print(form.errors)
            messages.error(request, 'Formulir tidak valid.')
            messages.error(request, form.errors)
    else:
        form = HutangForms()
        excel = ExcelUploadForm()
        data = HutangPiutang.objects.filter(owner=request.user).order_by('-tanggal','-id')
    context = {
        'form': form,
        'excel': excel,
        'data':data,
        "breadcrumb":{"parent":"Hutang Ortu","child":"Hutang Ortu"},
    }
    return render(request, 'hutang/hutang.html', context)

def DeleteHutang(request, pk):
    HutangPiutang.objects.get(id=pk, owner=request.user).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/hutang/')
#HUTANG PEGAWAI
def hutangPeg(request):
    data = HutPegawai.objects.filter(owner=request.user).order_by('-tanggal')
    apin = Karyawan.objects.filter(name='Apin').first()
    andi = Karyawan.objects.filter(name='Andi').first()
    oman = Karyawan.objects.filter(name='Oman').first()
    agung = Karyawan.objects.filter(name='Agung').first()
    amin = Karyawan.objects.filter(name='Pak Amin').first()
    anis = Karyawan.objects.filter(name='Pak Anis').first()
    today = timezone.now().date()
    #oman
    hutang_oman = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=oman).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_oman= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=oman).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_oman = piutang_oman - hutang_oman
    #apin
    hutang_apin = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=apin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_apin= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=apin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_apin = piutang_apin - hutang_apin
    #amin
    hutang_amin = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=amin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_amin= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=amin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_amin = piutang_amin - hutang_amin
    #andi
    hutang_andi = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=andi).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_andi= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=andi).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_andi = piutang_andi - hutang_andi
    #agung
    hutang_agung = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=agung).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_agung= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=agung).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_agung = piutang_agung - hutang_agung
    #anis
    hutang_anis = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=anis).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_anis= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=anis).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_anis = piutang_anis - hutang_anis
    if request.POST :
        form = HutangPegForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.save()
            messages.success(request, "Formulir Berhasil Dibuat")
            return redirect('/hutangpeg/')
        else:
            print(form.errors)
            messages.error(request, 'Formulir tidak valid.')
            messages.error(request, form.errors)
    else:
        form = HutangPegForms()
        data = HutPegawai.objects.filter(owner=request.user).order_by('-tanggal')
    people = [
        {"name": "Apin", "amount": sisa_apin},
        {"name": "Andi", "amount": sisa_andi},
        {"name": "Oman", "amount": sisa_oman},
        {"name": "Agung", "amount": sisa_agung},
        {"name": "anis", "amount": sisa_anis},
        {"name": "Pak Amin", "amount": sisa_amin},
    ]
    context = {
        'form': form,
        'data':data,
        'people':people,
        'oman':sisa_oman,
        'anis':sisa_anis,
        'agung':sisa_agung,
        'apin':sisa_apin,
        'andi':sisa_andi,
        'amin':sisa_amin,
        
        "breadcrumb":{"parent":"Hutang Pegawai","child":"HutangPegawai"},
    }
    return render(request, 'hutang_peg/hutang.html', context)

def UpdateHutangPeg(request, pk):
    instance = HutPegawai.objects.get(id=pk)
    if request.POST :
        form = HutangPegForms(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Formulir Berhasil Dibuat")
            return redirect('/hutangpeg/')
        else:
            print(form.errors)
            messages.error(request, 'Formulir tidak valid.')
            messages.error(request, form.errors)
    else:
        form = HutangPegForms()
        data = HutPegawai.objects.all().order_by('-tanggal','-id')
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Hutang Piutang Pegawai","child":"Hutang Pegawai"},
    }
    return render(request, 'hutang_peg/hutang.html', context)
    
@login_required(login_url='/accounts/')
def DeleteHutangPeg(request, pk):
    HutPegawai.objects.get(id=pk).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/hutangpeg/')

#TRANSAKSI
@login_required(login_url="/accounts/login/")
def transaksi(request):
    data = Transaksi.objects.filter(owner=request.user).order_by('-tanggal')
    total_pemasukan = (Transaksi.objects.filter(owner=request.user,transaksi_choice=Transaksi.PEMASUKAN).aggregate(total=Sum('jumlah'))['total'] or 0)
    total_pengeluaran = (Transaksi.objects.filter(owner=request.user,transaksi_choice=Transaksi.PENGELUARAN).aggregate(total=Sum('jumlah'))['total'] or 0)
    saldo = total_pemasukan - total_pengeluaran
    jumlah_transaksi = data.count()

    if request.POST :
        excel = ExcelUploadForm(request.POST, request.FILES)
        if excel.is_valid():
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                messages.error(request, 'File bukan berformat Excel (.xlsx)')
                return render(request, 'transaksi/index.html', {'excel': excel})

            df = pd.read_excel(excel_file, engine='openpyxl')

            for index, row in df.iterrows():
                try:
                    tanggal = pd.to_datetime(row['tanggal'], format='%Y-%m-%d')
                except ValueError:
                    messages.warning(request, f"Format tanggal tidak valid pada baris {index + 2}. Baris diabaikan.")
                    continue
                keterangan = row['keterangan']
                nama_kategori = row['kategori_id']  # Menambahkan kolom kategori
                pemasukan = row['pemasukan']
                pengeluaran = row['pengeluaran']
                owner_id = row['owner']  # Menambahkan kolom owner
                if pd.isna(pemasukan):
                    pemasukan = 0
                if pd.isna(pengeluaran):
                    pengeluaran = 0
                # Menentukan jenis transaksi berdasarkan pemasukan atau pengeluaran
                if pemasukan:
                    jenis_transaksi = Transaksi.PEMASUKAN
                    jumlah = pemasukan
                elif pengeluaran:
                    jenis_transaksi = Transaksi.PENGELUARAN
                    jumlah = pengeluaran
                else:
                    messages.warning(request, 'Kolom pemasukan atau pengeluaran harus diisi')
                    continue

                # Memeriksa kategori
                kategori, created = Kategori.objects.get_or_create(nama=nama_kategori)
                
                Transaksi.objects.create(
                    tanggal=tanggal,
                    keterangan=keterangan,
                    transaksi_choice=jenis_transaksi,
                    kategori=kategori,
                    jumlah=jumlah,
                    owner_id=owner_id
                )

        form = TransaksiForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.owner = request.user
            trform.save()
            messages.success(request, "Formulir Berhasil Dibuat")
            return redirect('/transaksi/')
        else:
            print(form.errors)
            messages.error(request, 'Formulir tidak valid.')
            messages.error(request, form.errors)
    form = TransaksiForms()
    excel = ExcelUploadForm()
     # Buat list (transaksi, form_instance) untuk modal update
    forms_list = [(t, TransaksiForms(instance=t)) for t in data]

    context = {
        'form': form,
        'excel': excel,
        'forms_list': forms_list,
        'data':data,
        'total_pemasukan':total_pemasukan,
        'total_pengeluaran':total_pengeluaran,
        'saldo':saldo,
        'jumlah_transaksi':jumlah_transaksi,
        "breadcrumb":{"parent":"Transaksi","child":"Transaksi"},
    }
    return render(request, 'transaksi/index.html', context)
@require_POST
@login_required
def delete_multiple_transaksi(request):
    ids = request.POST.getlist('ids')

    Transaksi.objects.filter(
        id__in=ids,
        owner=request.user
    ).delete()

    return JsonResponse({
        'status':'ok'
    })
@login_required(login_url='/accounts/')
def DeleteTr(request, pk):
    Transaksi.objects.get(id=pk).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/transaksi/')

@login_required(login_url='/accounts/login/')
def UpdateTr(request, pk):
    transaksi = get_object_or_404(Transaksi, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TransaksiForms(request.POST, instance=transaksi)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user  # pastikan owner tetap ter-set
            obj.save()
            messages.success(request, "Transaksi berhasil diperbarui.")
            return redirect('transaksi')
        else:
            messages.error(request, "Terdapat error pada form. Mohon periksa kembali.")
            print(form.errors)
    else:
        form = TransaksiForms(instance=transaksi)

    return render(request, 'transaksi/index.html', {'form': form, 'transaksi': transaksi})
#TABUNGAN
@login_required(login_url="/accounts/login/")
def tabungan_update_view(request, id):
    """
    Args:
        request:
        customer_id : The customer's ID that will be updated
    """

    # Get the customer
    try:
        # Get the customer to update
        tabungan = Tabungan.objects.get(id=id)
    except Tabungan.DoesNotExist:
        messages.error(request, 'Customer not found!', extra_tags="danger")
        return redirect('customers:customers_list')

    # Initialize the form with customer data
    form = TabunganForms(request.POST or None, instance=tabungan)

    if request.method == 'POST':
        if form.is_valid():
            # Save the form data
            form.save()
            messages.success(request, f'Customer: {customer.get_full_name()} updated successfully!', extra_tags="success")
            return redirect('customers:customers_list')
        else:
            messages.error(request, 'Invalid form submission!', extra_tags="danger")

    context = {
        "active_icon": "customers",
        "customer": customer,
        "form": form,
    }

    return render(request, "customers/customers_update.html", context=context)
#laporan
@login_required(login_url="/accounts/login/")
def laporan(request):
    from django.utils import timezone
    from datetime import timedelta, date as date_type
    from sales.models import Sale, SaleDetail
    from products.models import Product
    from django.db.models import Count

    today = timezone.localtime(timezone.now()).date()
    periode = request.GET.get('periode', 'harian')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Tentukan rentang tanggal berdasarkan periode
    if periode == 'harian':
        start_date = today
        end_date = today
    elif periode == 'mingguan':
        start_date = today - timedelta(days=6)
        end_date = today
    elif periode == 'custom' and start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today
            end_date = today
    else:
        start_date = today
        end_date = today

    # ------ Transaksi keuangan (Pemasukan / Pengeluaran) ------
    transactions = Transaksi.objects.filter(
        owner=request.user,
        tanggal__gte=start_date,
        tanggal__lte=end_date,
    ).order_by('-tanggal', '-id')

    transaksi_choice = request.GET.get('transaksi_choice')
    if transaksi_choice:
        transactions = transactions.filter(transaksi_choice=transaksi_choice)

    pemasukan = transactions.filter(transaksi_choice='P').aggregate(total=Sum('jumlah'))['total'] or 0
    pengeluaran = transactions.filter(transaksi_choice='L').aggregate(total=Sum('jumlah'))['total'] or 0
    saldo = pemasukan - pengeluaran

    # ------ Data Penjualan (Sales) ------
    sales_qs = Sale.objects.filter(
        owner=request.user,
        date_added__date__gte=start_date,
        date_added__date__lte=end_date,
    )
    total_sales_count = sales_qs.count()
    total_sales_revenue = sales_qs.aggregate(total=Sum('sub_total'))['total'] or 0

    # Top 5 produk terlaris dalam periode
    top_products = (
        SaleDetail.objects.filter(sale__in=sales_qs)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('total_detail'))
        .order_by('-total_qty')[:5]
    )

    # Data harian untuk grafik (selalu 7 hari ke belakang dari end_date)
    chart_labels = []
    chart_sales = []
    chart_income = []
    chart_expense = []
    num_days = min((end_date - start_date).days + 1, 30)
    for i in range(num_days - 1, -1, -1):
        day = end_date - timedelta(days=i)
        chart_labels.append(day.strftime('%d/%m'))
        daily_sale = Sale.objects.filter(owner=request.user, date_added__date=day).aggregate(total=Sum('sub_total'))['total'] or 0
        daily_income = Transaksi.objects.filter(owner=request.user, tanggal=day, transaksi_choice='P').aggregate(total=Sum('jumlah'))['total'] or 0
        daily_expense = Transaksi.objects.filter(owner=request.user, tanggal=day, transaksi_choice='L').aggregate(total=Sum('jumlah'))['total'] or 0
        chart_sales.append(float(daily_sale))
        chart_income.append(float(daily_income))
        chart_expense.append(float(daily_expense))

    import json as _json
    context = {
        'breadcrumb': {'parent': 'Laporan', 'child': 'Laporan Keuangan'},
        'transactions': transactions,
        'pemasukan': pemasukan,
        'pengeluaran': pengeluaran,
        'saldo': saldo,
        'periode': periode,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales_count': total_sales_count,
        'total_sales_revenue': total_sales_revenue,
        'top_products': list(top_products),
        'chart_labels_json': _json.dumps(chart_labels),
        'chart_sales_json': _json.dumps(chart_sales),
        'chart_income_json': _json.dumps(chart_income),
        'chart_expense_json': _json.dumps(chart_expense),
        'start_date_str': start_date.strftime('%Y-%m-%d'),
        'end_date_str': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'laporan/laporan.html', context)
def ChartReport(request):
    periode = request.GET.get('periode', 'harian')  # Default harian
    today = datetime.today()
    labels= []
    income_values = []
    expense_values = []

    if periode == 'harian':
        labels = [(today - timedelta(days=i)).strftime('%d-%m-%Y') for i in range(6, -1, -1)]
    elif periode == 'bulanan':
        labels = [(today.replace(day=1) - timedelta(days=30 * i)).strftime('%b %Y') for i in range(5, -1, -1)]
    elif periode == 'tahunan':
        labels = [(today.year - i) for i in range(5, -1, -1)]


    for label in labels:
        if periode == 'harian':
            date = datetime.strptime(label, '%d-%m-%Y').date()
            total_income = Transaksi.objects.filter(tanggal=date, transaksi_choice='P').aggregate(total=Sum('jumlah'))['total'] or 0
            total_expense = Transaksi.objects.filter(tanggal=date, transaksi_choice='L').aggregate(total=Sum('jumlah'))['total'] or 0

        elif periode == 'bulanan':
            start_date = datetime.strptime(label, '%b %Y').date()
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            total_income = Transaksi.objects.filter(tanggal__range=[start_date, end_date], transaksi_choice='P').aggregate(total=Sum('jumlah'))['total'] or 0
            total_expense = Transaksi.objects.filter(tanggal__range=[start_date, end_date], transaksi_choice='L').aggregate(total=Sum('jumlah'))['total'] or 0

        elif periode == 'tahunan':
            total_income = Transaksi.objects.filter(tanggal__year=label, transaksi_choice='P').aggregate(total=Sum('jumlah'))['total'] or 0
            total_expense = Transaksi.objects.filter(tanggal__year=label, transaksi_choice='L').aggregate(total=Sum('jumlah'))['total'] or 0

        income_values.append(total_income)
        expense_values.append(total_expense)

    data = {
        "labels": labels,
        "income_values": income_values,
        "expense_values": expense_values
    }

    return JsonResponse(data)

#print PDF
@login_required(login_url="/accounts/login/")
def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None

class ViewPDF(View):
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        transaksi = Transaksi.objects.all().order_by('tanggal')
        total_pengeluaran_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        total_pemasukan_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        sisa_saldo = total_pemasukan_tahunan - total_pengeluaran_tahunan

        data = {
        'data': transaksi,
        'pemasukan': total_pengeluaran_tahunan,
        'pengeluaran':total_pengeluaran_tahunan,
        'saldo':sisa_saldo
        
        }


        pdf = render_to_pdf('generatepdf.html', data)
        return HttpResponse(pdf, content_type='application/pdf')

class DownloadPDF(View):
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        transaksi = Transaksi.objects.all().order_by('tanggal')
        total_pengeluaran_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        total_pemasukan_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        sisa_saldo = total_pemasukan_tahunan - total_pengeluaran_tahunan

        data = {
        'data': transaksi,
        'pemasukan': total_pengeluaran_tahunan,
        'pengeluaran':total_pengeluaran_tahunan,
        'saldo':sisa_saldo

        }
        pdf = render_to_pdf('generatepdf.html', data)

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Invoice_%s.pdf" %("12341231")
        content = "attachment; filename='%s'" %(filename)
        response['Content-Disposition'] = content
        return response

#Wxport Excel
@login_required(login_url="/accounts/login/")
def import_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                messages.error(request, 'File bukan berformat Excel (.xlsx)')
                return render(request, 'transaksi/index.html', {'excel': form})

            df = pd.read_excel(excel_file, engine='openpyxl')

            for index, row in df.iterrows():
                try:
                    tanggal = pd.to_datetime(row['tanggal'], format='%Y-%m-%d')
                except ValueError:
                    messages.warning(request, f"Format tanggal tidak valid pada baris {index + 2}. Baris diabaikan.")
                    continue
                keterangan = row['keterangan']
                nama_kategori = row['kategori_id']  # Menambahkan kolom kategori
                pemasukan = row['pemasukan']
                pengeluaran = row['pengeluaran']
                owner_id = row['owner']  # Menambahkan kolom owner
                if pd.isna(pemasukan):
                    pemasukan = 0
                if pd.isna(pengeluaran):
                    pengeluaran = 0
                # Menentukan jenis transaksi berdasarkan pemasukan atau pengeluaran
                if pemasukan:
                    jenis_transaksi = Transaksi.PEMASUKAN
                    jumlah = pemasukan
                elif pengeluaran:
                    jenis_transaksi = Transaksi.PENGELUARAN
                    jumlah = pengeluaran
                else:
                    messages.warning(request, 'Kolom pemasukan atau pengeluaran harus diisi')
                    continue

                # Memeriksa kategori
                kategori, created = Kategori.objects.get_or_create(nama=nama_kategori)
                
                Transaksi.objects.create(
                    tanggal=tanggal,
                    keterangan=keterangan,
                    transaksi_choice=jenis_transaksi,
                    kategori=kategori,
                    jumlah=jumlah,
                    owner_id=owner_id
                )

            messages.success(request, 'Data berhasil diimpor.')
            return redirect('transaksi')
    else:
        form = ExcelUploadForm()
    return render(request, 'transaksi/index.html', {'excel': form})
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url="/accounts/login/")
def AnalasisChart(request):
    # Ambil semua kategori dari model
    categories = Kategori.objects.all()
    data = []

    # Hitung total per kategori yang ada
    for kategori in categories:
        total_amount = (
            Transaksi.objects.filter(kategori=kategori, owner=request.user)
            .aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        )
        data.append({'kategori': kategori.nama, 'jumlah': float(total_amount)})

    # Tambahkan kategori None → "Pengeluaran"
    total_none = (
        Transaksi.objects.filter(kategori__isnull=True, owner=request.user)
        .aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    )
    if total_none > 0:
        data.append({'kategori': 'Pengeluaran', 'jumlah': float(total_none)})

    # Siapkan data untuk chart donut
    labels_don = [item['kategori'] for item in data]
    values_don = [float(item['jumlah']) for item in data]
    return JsonResponse({
        'labels_don': labels_don,
        'values_don': values_don,
    })


logger = logging.getLogger(__name__)

def chart_data(request, period='monthly'):
    try:
        qs = Transaksi.objects.filter(owner=request.user)

        if period == 'daily':
            qs = qs.annotate(period_date=TruncDate('tanggal'))
        else:  # monthly
            qs = qs.annotate(period_date=TruncMonth('tanggal'))

        qs = (qs
              .values('period_date', 'transaksi_choice')
              .annotate(total_jumlah=Coalesce(Sum('jumlah'), Value(0)))
              .order_by('period_date'))

        # mapping unique dates/months
        unique_dates = []
        for row in qs:
            d = row.get('period_date')
            if d is not None and d not in unique_dates:
                unique_dates.append(d)

        idx_map = {d: i for i, d in enumerate(unique_dates)}
        income_values = [0.0] * len(unique_dates)
        expense_values = [0.0] * len(unique_dates)

        for row in qs:
            d = row.get('period_date')
            if d is None:
                continue
            i = idx_map[d]
            amount = float(row.get('total_jumlah') or 0.0)
            choice = row.get('transaksi_choice')
            if choice == 'P':
                income_values[i] += amount
            elif choice == 'L':
                expense_values[i] += amount

        # labels
        if period == 'monthly':
            labels = [f"{calendar.month_abbr[d.month]} {d.year}" for d in unique_dates]
        elif period == 'daily':
            labels = [d.isoformat() for d in unique_dates]
        else:  # yearly
            labels = [str(d.year) for d in unique_dates]

    except Exception as e:
        logger.exception("Chart data fallback due to error: %s", e)
        # fallback manual
        qs = Transaksi.objects.filter(owner=request.user).values_list('tanggal', 'jumlah', 'transaksi_choice')
        grouped_income = defaultdict(float)
        grouped_expense = defaultdict(float)

        for t, jumlah, choice in qs:
            if t is None:
                continue
            d = t.date() if hasattr(t, 'date') else t
            if choice == 'P':
                grouped_income[d] += float(jumlah or 0)
            elif choice == 'L':
                grouped_expense[d] += float(jumlah or 0)

        all_dates = sorted(set(list(grouped_income.keys()) + list(grouped_expense.keys())))
        labels = [d.isoformat() for d in all_dates]
        income_values = [grouped_income.get(d, 0.0) for d in all_dates]
        expense_values = [grouped_expense.get(d, 0.0) for d in all_dates]

    return JsonResponse({
        'labels': labels,
        'income_values': income_values,
        'expense_values': expense_values
    })

def fetch_resources(uri, rel):
    path = os.path.join(uri.replace(settings.STATIC_URL, ""))
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
# page layout views
class GenerateInvoice(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            order_db = Transaksi.objects.get(id=pk, owner= request.user, payment_status = 1)  
            #you can filter using order_id as well
        except:
            return HttpResponse("505 Not Found")
        data = {
            'jumlah': order_db.jumlah,
            'kategori': order_db.kategori,
            'transaksi_choice': order_db.transaksi_choice,
            'id': order_db.id,
            'tanggal': str(order_db.tanggal),
            'name': order_db.user.name,
            'order': order_db,
        }
        pdf = render_to_pdf('invoice.html', data)
        #return HttpResponse(pdf, content_type='application/pdf')

        # force download
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Invoice_%s.pdf" %(data['order_id'])
            content = "inline; filename='%s'" %(filename)
            #download = request.GET.get("download")
            #if download:
            content = "attachment; filename=%s" %(filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
@login_required(login_url="/accounts/login/")
def page_layout_boxed(request):
    context ={"layout":"box-layout","breadcrumb":{"parent":"Page Layout","child":"Box Layout"}}
    return render(request,'page_layout/boxed/box-layout.html',context)

@login_required(login_url="/accounts/login/")
def page_layout_rtl(request):
    context={"layout":"rtl","breadcrumb":{"parent":"Page Layout","child":"RTL"}}
    return render(request,'page_layout/RTL/layout-rtl.html',context)

@login_required(login_url="/accounts/login/")
def page_layout_dark(request):
    context ={"layout":"dark-only","breadcrumb":{"parent":"Page Layout","child":"Layout Dark"}}
    return render(request,'page_layout/dark_layout/layout-dark.html',context)

@login_required(login_url="/accounts/login/")
def page_layout_hide_nav_scroll(request):
    context={"breadcrumb":{"parent":"Page Layout","child":"Hide Menu On Scroll"}}
    return render(request,'page_layout/hide_nav_scroll/hide-on-scroll.html',context)

@login_required(login_url="/accounts/login/")
def page_layout_footer_light(request):
    context={"breadcrumb":{"parent":"Page Layout","child":"Footer Light"}}
    return render(request,'page_layout/footer_light/footer-light.html',context)

@login_required(login_url="/accounts/login/")
def page_layout_footer_dark(request):
    context={"footer":"footer-dark","breadcrumb":{"parent":"Page Layout","child":"Footer Dark"}}
    return render(request,'page_layout/footer_dark/footer-dark.html',context)

@login_required(login_url="/accounts/login/")
def page_layout_footer_fixed(request):
    context={"footer":"footer-fix","breadcrumb":{"parent":"Page Layout","child":"Footer Fixed"}}
    return render(request,'page_layout/footer_fixed/footer-fixed.html',context)

# to do views

@login_required(login_url="/accounts/login/")
def to_do_view(request):
    context={"breadcrumb":{"parent":"Apps","child":"To Do"}}
    return render(request,'to_do/to-do.html',context)

@login_required(login_url="/accounts/login/")
def to_do_database(request):
    tasks = Task.objects.all()

    form = TaskForm()
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('/to_do_database')

    completedTasks = True
    for t in tasks:
        if t.complete == False:
            completedTasks = False

    context = {'tasks': tasks, 'form': form,'completedTasks': completedTasks, "breadcrumb":{"parent":"Todo", "child":"Todo with database"}}
    context = {'tasks': tasks, 'form': form,'completedTasks': completedTasks, "breadcrumb":{"parent":"Todo", "child":"Todo with database"}}

    return render(request,'to_do_database/to-do-database.html',context)
    
@login_required(login_url="/accounts/login/")
def markAllComplete(request):
    allTasks = Task.objects.all()
    for oneTask in allTasks:
        oneTask.complete = True
        oneTask.save()
    return HttpResponseRedirect("/to_do_database")


@login_required(login_url="/accounts/login/")
def markAllIncomplete(request):
    allTasks = Task.objects.all()
    for oneTask in allTasks:
        oneTask.complete = False
        oneTask.save()
    return HttpResponseRedirect("/to_do_database")


@login_required(login_url="/accounts/login/")
def deleteTask(request, pk):
    item = Task.objects.get(id=pk)
    
    #if request.method == "POST":
    item.delete()
    return HttpResponseRedirect("/to_do_database")


@login_required(login_url="/accounts/login/")
def updateTask(request, pk):
    task = Task.objects.get(id=pk)
    if task.complete == False:
        task.complete = True
        task.save()
    else:
        task.complete = False
        task.save()

    return HttpResponseRedirect("/to_do_database")

@login_required(login_url="/accounts/login/")
def tabungan(request):
    data = Tabungan.objects.all().order_by('-date')
    if request.POST :
        form = TabunganForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.save()
            messages.success(request, "Formulir Berhasil Dibuat")
            return redirect('/tabungan/')
        else:
            print(form.errors)
            messages.error(request, 'Formulir tidak valid.')
            messages.error(request, form.errors)
    else:
        form = TabunganForms()
        data = Tabungan.objects.all().order_by('-date','-id')
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Tabungan","child":"Transaksi"},
    }
    return render(request, 'tabungan/tabung.html', context)


# ==========================================
# CHIMIAI ASSISTANT INTEGRATION
# ==========================================

import requests
import json

def build_pos_data_context(user=None):
    """
    Mengumpulkan dan meringkas data real-time POS Rosok untuk dijadikan konteks ChimiAI.
    """
    now = timezone.now()
    today = now.date()
    start_of_month = today.replace(day=1)

    # 1. Kas Operasional
    trans_qs = Transaksi.objects.all()
    if user and user.is_authenticated:
        trans_user = trans_qs.filter(owner=user)
        if trans_user.exists():
            trans_qs = trans_user

    pemasukan_total = trans_qs.filter(transaksi_choice=Transaksi.PEMASUKAN).aggregate(s=Sum('jumlah'))['s'] or 0
    pengeluaran_total = trans_qs.filter(transaksi_choice=Transaksi.PENGELUARAN).aggregate(s=Sum('jumlah'))['s'] or 0
    kas_bersih = float(pemasukan_total) - float(pengeluaran_total)

    pemasukan_bulan_ini = trans_qs.filter(transaksi_choice=Transaksi.PEMASUKAN, tanggal__gte=start_of_month).aggregate(s=Sum('jumlah'))['s'] or 0
    pengeluaran_bulan_ini = trans_qs.filter(transaksi_choice=Transaksi.PENGELUARAN, tanggal__gte=start_of_month).aggregate(s=Sum('jumlah'))['s'] or 0

    # 2. Profit & Olahan Rosok (Profito2)
    profit_qs = Profito2.objects.all().order_by('-tanggal')
    profit_count = profit_qs.count()
    total_revenue_prof = profit_qs.aggregate(s=Sum('total_revenue'))['s'] or 0
    total_hpp_prof = profit_qs.aggregate(s=Sum('total_hpp'))['s'] or 0
    total_profit_prof = profit_qs.aggregate(s=Sum('profit'))['s'] or 0
    total_tabungan_prof = profit_qs.aggregate(s=Sum('tabungan_total'))['s'] or 0

    recent_profito = []
    for item in profit_qs[:7]:
        recent_profito.append(
            f"- Barang: {item.nama_barang} | Tgl: {item.tanggal} | Berat In: {item.berat_input} kg | Berat Out: {item.berat_output or 0} kg | "
            f"HPP/kg: Rp {int(item.hpp_per_kg or 0):,} | Jual/kg: Rp {int(item.harga_jual_per_kg or 0):,} | Revenue: Rp {int(item.total_revenue or 0):,} | "
            f"Profit: Rp {int(item.profit or 0):,} (Margin: {item.profit_margin or 0}%) | Tabungan: Rp {int(item.tabungan_total or 0):,}"
        )

    # 3. Stok Barang
    stocks = Stock.objects.select_related('product').all()
    total_items_count = stocks.count()
    total_stok_kg = 0
    stock_summary = []
    for st in stocks[:10]:
        total_stok_kg += float(st.quantity or 0)
        stock_summary.append(f"- {st.product.name} (Kode: {st.product.code or '-'}): {st.quantity} kg/pcs")

    # 4. Transaksi Sales & Detail
    sales_qs = Sale.objects.all()
    if user and user.is_authenticated:
        sales_user = sales_qs.filter(owner=user)
        if sales_user.exists():
            sales_qs = sales_user
    sales_count = sales_qs.count()
    total_penjualan_val = sales_qs.aggregate(s=Sum('sub_total'))['s'] or 0
    total_dibayar_val = sales_qs.aggregate(s=Sum('amount_payed'))['s'] or 0

    # 5. Hutang & Piutang
    hutang_qs = HutangPiutang.objects.all()
    if user and user.is_authenticated:
        h_user = hutang_qs.filter(owner=user)
        if h_user.exists():
            hutang_qs = h_user

    total_hutang_toko = hutang_qs.filter(hutang_choice=HutangPiutang.HUTANG).aggregate(s=Sum('jumlah'))['s'] or 0
    total_piutang_toko = hutang_qs.filter(hutang_choice=HutangPiutang.PIUTANG).aggregate(s=Sum('jumlah'))['s'] or 0

    hutpeg_qs = HutPegawai.objects.all()
    total_hutang_pegawai = hutpeg_qs.filter(hutang_choice=HutPegawai.HUTANG).aggregate(s=Sum('jumlah'))['s'] or 0
    total_piutang_pegawai = hutpeg_qs.filter(hutang_choice=HutPegawai.PIUTANG).aggregate(s=Sum('jumlah'))['s'] or 0

    context_str = f"""
[DATA PENJUALAN & KEUANGAN REAL-TIME POS ROSOK]
Tanggal Laporan: {today.strftime('%d-%m-%Y')}

1. KAS OPERASIONAL TOKO:
- Total Pemasukan Kas: Rp {int(pemasukan_total):,}
- Total Pengeluaran Kas: Rp {int(pengeluaran_total):,}
- Saldo Kas Bersih: Rp {int(kas_bersih):,}
- Pemasukan Bulan Ini: Rp {int(pemasukan_bulan_ini):,}
- Pengeluaran Bulan Ini: Rp {int(pengeluaran_bulan_ini):,}

2. OLAHAN ROSOK & ANALISIS PROFIT (PROFITO):
- Total Olahan Selesai: {profit_count} transaksi batch
- Total Revenue/Omset Olahan: Rp {int(total_revenue_prof):,}
- Total HPP Olahan: Rp {int(total_hpp_prof):,}
- Total Profit Bersih Olahan: Rp {int(total_profit_prof):,}
- Total Akumulasi Tabungan Toko: Rp {int(total_tabungan_prof):,}
- Data Olahan Rosok Terbaru:
{chr(10).join(recent_profito) if recent_profito else '  (Belum ada data olahan)'}

3. TRANSAKSI BARANG MASUK & KELUAR:
- Total Transaksi Sale: {sales_count} transaksi
- Total Nilai Transaksi (Subtotal): Rp {int(total_penjualan_val):,}
- Total Pembayaran Cash Terima: Rp {int(total_dibayar_val):,}

4. PERSEDIAAN STOK GUDANG:
- Total Jenis Barang: {total_items_count} item
- Total Estimasi Berat Stok: {total_stok_kg:.2f} kg
- Rincian Stok Utama:
{chr(10).join(stock_summary) if stock_summary else '  (Belum ada data stok)'}

5. STATUS HUTANG & PIUTANG:
- Total Hutang Toko (Kewajiban Bayar ke Supplier/Seller): Rp {int(total_hutang_toko):,}
- Total Piutang Toko (Tagihan ke Pelanggan): Rp {int(total_piutang_toko):,}
- Total Hutang Pegawai: Rp {int(total_hutang_pegawai):,}
- Total Piutang Pegawai: Rp {int(total_piutang_pegawai):,}
"""
    return context_str.strip()


@login_required(login_url="/accounts/login/")
@require_POST
def chimi_ai_chat(request):
    """
    API endpoint untuk memproses pertanyaan ke ChimiAI via Gemini Flash API.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'status': 'error', 'message': 'Pesan tidak boleh kosong.'}, status=400)

        # 1. Kumpulkan context data dari database
        pos_context = build_pos_data_context(request.user)

        # 2. Susun System Prompt & Prompt Utama
        system_prompt = (
            "Kamu adalah Asisten Pintar untuk Sistem Informasi POS Rosok (Kasir & Manajemen Barang Bekas) saya namakan kamu ChimiAI.\n\n"
            "Tugas utama:\n"
            "1. Membantu admin/pemilik toko menganalisis data penjualan, stok, dan transaksi berdasarkan DATA KONTEKS yang disediakan di setiap permintaan.\n"
            "2. Jawablah pertanyaan pengguna secara singkat, padat, jelas, akurat, dan ramah menggunakan Bahasa Indonesia yang wajar.\n\n"
            "Aturan Ketat:\n"
            "- HANYA gunakan informasi yang ada di dalam [DATA PENJUALAN] yang diberikan.\n"
            "- Jika jawaban tidak ada di dalam data yang diberikan, katakan dengan sopan: \"Maaf, data tersebut tidak tersedia dalam ringkasan penjualan saat ini.\"\n"
            "- Jangan membuat asumsi, estimasi, atau jawaban fiktif sendiri yang tidak didukung data.\n"
            "- Jika pengguna menanyakan unit barang (seperti kg, pcs, atau ton) atau mata uang (Rp), cantumkan dengan jelas.\n"
            "- Hindari memberikan jawaban yang terlalu panjang atau bertele-tele."
        )

        full_prompt = (
            f"{system_prompt}\n\n"
            f"[DATA PENJUALAN]\n{pos_context}\n\n"
            f"[PERTANYAAN PENGGUNA]\n{user_message}"
        )

        # 3. Request ke Gemini Flash API dengan Fallback
        endpoints = [
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
        ]
        api_key = os.getenv("GEMINI_API_KEY")

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": api_key
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ]
        }

        reply_text = None
        last_error = None

        for endpoint_url in endpoints:
            try:
                response = requests.post(endpoint_url, headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    candidates = res_json.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        reply_text = "".join([p.get('text', '') for p in parts]).strip()
                        break
                else:
                    last_error = f"Status {response.status_code}: {response.text[:150]}"
            except Exception as req_err:
                last_error = str(req_err)

        if reply_text:
            return JsonResponse({
                'status': 'success',
                'reply': reply_text,
                'timestamp': timezone.now().strftime('%H:%M')
            })
        else:
            print(f"Gemini API All Fallbacks Failed: {last_error}")
            return JsonResponse({
                'status': 'error',
                'message': 'Maaf, layanan AI sedang padat saat ini. Silakan coba 10 detik lagi.'
            }, status=500)

    except Exception as e:
        print(f"ChimiAI Exception: {e}")
        return JsonResponse({'status': 'error', 'message': f'Terjadi kesalahan internal: {str(e)}'}, status=500)


@login_required(login_url="/accounts/login/")
def chimi_ai_page(request):
    """
    Halaman utama workspace ChimiAI Assistant
    """
    now = timezone.now()
    today = now.date()

    # Stat ringkas untuk card atas
    trans_qs = Transaksi.objects.all()
    pemasukan = trans_qs.filter(transaksi_choice=Transaksi.PEMASUKAN).aggregate(s=Sum('jumlah'))['s'] or 0
    pengeluaran = trans_qs.filter(transaksi_choice=Transaksi.PENGELUARAN).aggregate(s=Sum('jumlah'))['s'] or 0
    kas_bersih = float(pemasukan) - float(pengeluaran)

    profit_qs = Profito2.objects.all()
    total_profit = profit_qs.aggregate(s=Sum('profit'))['s'] or 0
    total_tabungan = profit_qs.aggregate(s=Sum('tabungan_total'))['s'] or 0

    stok_count = Stock.objects.count()

    context = {
        'kas_bersih': kas_bersih,
        'total_profit': total_profit,
        'total_tabungan': total_tabungan,
        'stok_count': stok_count,
        'breadcrumb': {"parent": "Analisis AI", "child": "ChimiAI Assistant"},
    }
    return render(request, 'chimi_ai/page.html', context)


@login_required(login_url="/accounts/login/")
def get_chimi_ai_summary(request):
    """
    API ringan untuk mengambil quick stats yang dipakai oleh widget ChimiAI
    """
    trans_qs = Transaksi.objects.all()
    pemasukan = trans_qs.filter(transaksi_choice=Transaksi.PEMASUKAN).aggregate(s=Sum('jumlah'))['s'] or 0
    pengeluaran = trans_qs.filter(transaksi_choice=Transaksi.PENGELUARAN).aggregate(s=Sum('jumlah'))['s'] or 0
    kas_bersih = float(pemasukan) - float(pengeluaran)

    profit_qs = Profito2.objects.all()
    total_profit = profit_qs.aggregate(s=Sum('profit'))['s'] or 0

    hutang_qs = HutangPiutang.objects.all()
    total_hutang = hutang_qs.filter(hutang_choice=HutangPiutang.HUTANG).aggregate(s=Sum('jumlah'))['s'] or 0
    total_piutang = hutang_qs.filter(hutang_choice=HutangPiutang.PIUTANG).aggregate(s=Sum('jumlah'))['s'] or 0

    return JsonResponse({
        'kas_bersih': kas_bersih,
        'total_profit': total_profit,
        'total_hutang': total_hutang,
        'total_piutang': total_piutang,
    })

