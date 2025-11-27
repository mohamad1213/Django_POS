from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.http import JsonResponse, HttpResponse
import openpyxl
from datetime import datetime, date
from django.db import transaction
import re
from datetime import datetime, time
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from .helpers import *
from django.shortcuts import render
from collections import defaultdict
from .models import *
from .forms import *
from django.contrib import messages
import locale
from datetime import datetime, timedelta
from babel.numbers import format_currency
# Set the locale to Indonesian (ID) format
# locale.setlocale(locale.LC_ALL, 'id_ID')
from django.db.models import Q 
from django.template.loader import get_template
from django.shortcuts import render
from .forms import ExcelUploadForm
from io import BytesIO
# dashboard pages
from django.db.models import Sum
from django.utils import timezone
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from .models import *
from io import BytesIO
from xhtml2pdf import pisa
from django.views import View
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models.functions import TruncDate
#Dashboard
from django.db.models import Sum
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.utils import timezone
from sales.models import SaleDetail
## BERANDA PAGE
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, formset_factory
from .models import StockIn
from .forms import StockInForm
from django.http import JsonResponse
from .models import Product
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.shortcuts import render
from django.db.models import Sum, Value
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone
import calendar, json
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
    products = Product.objects.all()
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
    stockins = StockIn.objects.select_related("product", "received_by").order_by("-received_at")
    
    return render(request, "stok/stockin_list.html", {"stockins": stockins,"breadcrumb": {"parent": "Stok Barang", "child": "Stok Barang"},})
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



def get_product_summary(request):
    data = (
        SaleDetail.objects
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('product__name')
    )

    product_names = [d['product__name'] for d in data]
    product_totals = [d['total_qty'] for d in data]

    return JsonResponse({
        'product_names': product_names,
        'product_totals': product_totals
    })
@login_required(login_url="/accounts/login/")
def indexPage(request):
    today = timezone.localtime(timezone.now()).date()

    # Ambil data terbaru (5)
    data = Transaksi.objects.all().order_by('-tanggal')[:5]

    # Hitung jumlah total rows (untuk debug)
    count = Transaksi.objects.count()
    print("Total transaksi:", count)

    try:
        totals_per_product = (
            SaleDetail.objects
            .values('product__name')  # nama produk
            .annotate(total_qty=Sum('quantity'))  # jumlah total
            .order_by('-total_qty')
        )
        # Buat list untuk chart
        product_names = [p['product__name'] for p in totals_per_product]
        product_totals = [p['total_qty'] for p in totals_per_product]
        total_pemasukan_harian = (
            Transaksi.objects
            .filter(tanggal__date=today, transaksi_choice='P')
            .aggregate(total=Sum('jumlah'))['total'] or 0
        )

        total_pengeluaran_harian = (
            Transaksi.objects
            .filter(tanggal__date=today, transaksi_choice='L')
            .aggregate(total=Sum('jumlah'))['total'] or 0
        )

    except Exception as e:
        # Bila terjadi error (mis. DB tidak support __date), jatuhkan ke opsi B
        print("Opsi A gagal:", e)

        # =========================
        # Opsi B: rentang waktu (paling aman)
        # =========================
        tz = timezone.get_current_timezone()
        start_dt = datetime.combine(today, time.min).replace(tzinfo=tz)
        end_dt = datetime.combine(today, time.max).replace(tzinfo=tz)

        total_pemasukan_harian = (
            Transaksi.objects
            .filter(tanggal__gte=start_dt, tanggal__lte=end_dt, transaksi_choice='P')
            .aggregate(total=Sum('jumlah'))['total'] or 0
        )

        total_pengeluaran_harian = (
            Transaksi.objects
            .filter(tanggal__gte=start_dt, tanggal__lte=end_dt, transaksi_choice='L')
            .aggregate(total=Sum('jumlah'))['total'] or 0
        )

    # =========================
    # Bulanan & Tahunan (gunakan lookup month/year)
    # =========================
    total_pemasukan_bulanan = (
        Transaksi.objects
        .filter(tanggal__month=today.month, transaksi_choice='P')
        .aggregate(total=Sum('jumlah'))['total'] or 0
    )

    total_pengeluaran_bulanan = (
        Transaksi.objects
        .filter(tanggal__month=today.month, transaksi_choice='L')
        .aggregate(total=Sum('jumlah'))['total'] or 0
    )

    total_pemasukan_tahunan = (
        Transaksi.objects
        .filter(tanggal__year=today.year, transaksi_choice='P')
        .aggregate(total=Sum('jumlah'))['total'] or 0
    )

    total_pengeluaran_tahunan = (
        Transaksi.objects
        .filter(tanggal__year=today.year, transaksi_choice='L')
        .aggregate(total=Sum('jumlah'))['total'] or 0
    )

    # Sisa / cashflow
    sisa_saldo = total_pemasukan_tahunan - total_pengeluaran_tahunan
    sisa_cashflow_harian = total_pemasukan_harian - total_pengeluaran_harian
    sisa_cashflow_bulanan = total_pemasukan_bulanan - total_pengeluaran_bulanan
    sisa_cashflow_tahunan = total_pemasukan_tahunan - total_pengeluaran_tahunan

    # Hutang/piutang
    total_hutang = (
        HutangPiutang.objects
        .filter(tanggal__year=today.year, hutang_choice='H')
        .aggregate(total=Sum('jumlah'))['total'] or 0
    )

    total_piutang = (
        HutangPiutang.objects
        .filter(tanggal__year=today.year, hutang_choice='P')
        .aggregate(total=Sum('jumlah'))['total'] or 0
    )
    
    sisa_hutang = total_piutang - total_hutang

    context = {
        "breadcrumb": {"parent": "Dashboard", "child": "Dashboard"},
        'total_pemasukan_harian': total_pemasukan_harian,
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
        'sisa_saldo': sisa_saldo,
        'data': data,
        'count': count,
        'product_names': product_names,
        'product_totals': product_totals,
    }

    return render(request, 'general/dashboard/default/index.html', context)

#PROFIT
@login_required(login_url="/accounts/login/")
def profit_create(request):
    if request.method == 'POST':
        form = ProfitForms(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Formulir Berhasil Dibuat")
            return redirect('profit')  # ganti sesuai nama url list
    else:
        form = ProfitForms()
    
    return render(request, 'profit/tambah_profit.html', {'form': form})

@login_required(login_url="/accounts/login/")
def profit(request):
    data = Profito2.objects.all()
    profit_today = profit_today_value()
    formatted = format_currency(profit_today, 'IDR', locale='id_ID')
    datenow = timezone.now().strftime("%d-%m-%Y")
    
    context = {
        'data':data,
        'datenow':datenow,
        'profit_today':formatted[:-3],
        "breadcrumb":{"parent":"Profit","child":"Profit"},
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
    data = HutangPiutang.objects.all().order_by('-tanggal')
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
        data = HutangPiutang.objects.all().order_by('-tanggal','-id')
    context = {
        'form': form,
        'excel': excel,
        'data':data,
        "breadcrumb":{"parent":"Hutang Ortu","child":"Hutang Ortu"},
    }
    return render(request, 'hutang/hutang.html', context)

def DeleteHutang(request, pk):
    HutangPiutang.objects.get(id=pk).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/hutang/')
#HUTANG PEGAWAI
def hutangPeg(request):
    data = HutPegawai.objects.all().order_by('-tanggal')
    apin = Karyawan.objects.get(name='Apin')
    andi = Karyawan.objects.get(name='Andi')
    oman = Karyawan.objects.get(name='Oman')
    agung = Karyawan.objects.get(name='Agung')
    amin = Karyawan.objects.get(name='Pak Amin')
    anis = Karyawan.objects.get(name='Pak Anis')
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
        data = HutPegawai.objects.all().order_by('-tanggal')
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
    data = Transaksi.objects.all().order_by('-id')
        
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
        "breadcrumb":{"parent":"Transaksi","child":"Transaksi"},
    }
    return render(request, 'transaksi/index.html', context)

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
def laporan(request):
    data = Transaksi.objects.all().order_by('-tanggal','-id')
    pemasukan = pengeluaran = saldo = 0
    if request.method == 'GET':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        transaksi_choice = request.GET.get('transaksi_choice')

        # Check if both start date and end date are provided
        if start_date and end_date:
            transactions = Transaksi.objects.filter(
                tanggal__gte=start_date,
                tanggal__lte=end_date
            )
            if transaksi_choice:  # Filter by transaksi_choice if provided
                transactions = transactions.filter(transaksi_choice=transaksi_choice)

            transactions = transactions.order_by('-tanggal', '-id')
            pemasukan = transactions.filter(transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
            pengeluaran = transactions.filter(transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
            saldo = pemasukan - pengeluaran
            return render(request, 'laporan/laporan.html', {
                'transactions': transactions,
                'pemasukan': pemasukan,
                'pengeluaran': pengeluaran,
                'saldo': saldo
            })
    context = {
        'data': data,
        'pemasukan': pemasukan,
        'pengeluaran': pengeluaran,
        'saldo': saldo
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
    print(categories)
    data = []

    # Hitung total per kategori yang ada
    for kategori in categories:
        total_amount = (
            Transaksi.objects.filter(kategori=kategori)
            .aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        )
        data.append({'kategori': kategori.nama, 'jumlah': float(total_amount)})

    # Tambahkan kategori None → "Pengeluaran"
    total_none = (
        Transaksi.objects.filter(kategori__isnull=True)
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


from django.http import JsonResponse
from django.db.models import Sum, Value
from django.db.models.functions import TruncDate, TruncMonth, Coalesce
from django.utils import timezone
from collections import defaultdict
import calendar, logging

from .models import Transaksi

logger = logging.getLogger(__name__)

def chart_data(request, period='monthly'):
    """
    period: 'daily', 'monthly', 'yearly'
    """
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
            order_db = Transaksi.objects.get(id = pk, user = request.user, payment_status = 1)     #you can filter using order_id as well
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
