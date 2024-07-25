from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.http import JsonResponse, HttpResponse
import openpyxl
from django.http import HttpResponse
from django.shortcuts import render
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
import sweetify

#Dashboard
@login_required(login_url="/accounts/login/")
def indexPage(request):
    data = Transaksi.objects.all().order_by('-tanggal')[:6]
    count = Transaksi.objects.all().order_by('-tanggal')
    calculate = Transaksi.objects.filter(transaksi_choice='P')
    for u in calculate :
        calculate = u.calculate_profit_loss
    today = timezone.now().date()
    total_pemasukan_harian = Transaksi.objects.filter(tanggal=today, transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pemasukan_bulanan = Transaksi.objects.filter(tanggal__month=today.month, transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pengeluaran_harian = Transaksi.objects.filter(tanggal=today, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pengeluaran_bulanan = Transaksi.objects.filter(tanggal__month=today.month, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pengeluaran_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pemasukan_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_saldo = total_pemasukan_tahunan - total_pengeluaran_tahunan
    total_hutang = HutangPiutang.objects.filter(tanggal__year=today.year, hutang_choice='H').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_piutang = HutangPiutang.objects.filter(tanggal__year=today.year, hutang_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_hutang = total_piutang - total_hutang
    sisa_cashflow_harian = total_pemasukan_harian - total_pengeluaran_harian
    sisa_cashflow_bulanan = total_pemasukan_bulanan - total_pengeluaran_bulanan
    sisa_cashflow_tahunan = total_pemasukan_tahunan - total_pengeluaran_tahunan
    context={
        "breadcrumb":{"parent":"Dashboard","child":"Dashboard"},
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
        'data':data,
        'count':count,
        'calculate':calculate
        }

    return render(request,'general/dashboard/default/index.html',context)

#PROFIT
@login_required(login_url="/accounts/login/")
def profit(request):
    data = Profito.objects.all().order_by('-date')
    if request.POST :
        form = ProfitForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.owner = request.user
            trform.save()
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/classroom/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    else:
        form = ProfitForms()
        data = Profito.objects.all().order_by('-date','-id')
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Profit","child":"Transaksi"},
    }
    return render(request, 'profit/profit.html', context)

@login_required(login_url='/accounts/')
def UpdatePr(request, pk):
    try :
        data = Profito.objects.get(id=pk)
    except Profito.DoesNotExist:
        messages.error(request, 'Transaksi not found!', extra_tags="danger")
        return redirect('profit')
    if request.POST :
        form = ProfitForms(request.POST or None, instance=data)
        # form = TransaksiForms(request.POST, instance=formData)
        if form.is_valid():    
            # trform = form.save(commit=False)
            form.instance.user =request.user
            jumlah_brg =form.cleaned_data.get('jumlah_brg')
            nama_suplayer =form.cleaned_data.get('nama_suplayer')
            harga_jual =form.cleaned_data.get('harga_jual')
            harga_beli =form.cleaned_data.get('harga_beli')
            date =form.cleaned_data.get('date')
            description =form.cleaned_data.get('description')
            form.owner = request.user
            form.save()
            user = request.user
            applicant = Profito.objects.get(user=user)
            applicant.jumlah_brg = jumlah_brg
            applicant.nama_suplayer = nama_suplayer
            applicant.harga_jual=harga_jual
            applicant.harga_beli=harga_beli
            applicant.date=date
            applicant.description =description
            applicant.save()
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/profit/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    context = {
    'form': form,
    "breadcrumb":{"parent":"profit","child":"Profit"},
    }
    return render(request, 'profit/profit.html', context)

def DeleteProf(request, pk):
    Profito.objects.get(id=pk).delete()
    sweetify.success(request, "Form Successfully Deleted")  
    return redirect('/profit/')
    
#HUTANG ORTU
@login_required(login_url="/accounts/login/")
def hutang(request):
    data = HutangPiutang.objects.all().order_by('-tanggal')
    if request.POST :
        excel = ExcelUploadForm(request.POST, request.FILES)
        if excel.is_valid():
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                sweetify.error(request, 'File bukan berformat Excel (.xlsx)')
                return render(request, 'transaksi/index.html', {'excel': excel})

            df = pd.read_excel(excel_file, engine='openpyxl')

            for index, row in df.iterrows():
                try:
                    tanggal = pd.to_datetime(row['tanggal'], format='%Y-%m-%d')
                except ValueError:
                    sweetify.warning(request, f"Format tanggal tidak valid pada baris {index + 2}. Baris diabaikan.")
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
                    sweetify.warning(request, 'Kolom pemasukan atau pengeluaran harus diisi')
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
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/hutang/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    else:
        form = HutangForms()
        excel = ExcelUploadForm()
        data = HutangPiutang.objects.all().order_by('-tanggal','-id')
    context = {
        'form': form,
        'excel': excel,
        'data':data,
        "breadcrumb":{"parent":"Hutang Piutang","child":"Transaksi"},
    }
    return render(request, 'hutang/hutang.html', context)

def DeleteHutang(request, pk):
    HutangPiutang.objects.get(id=pk).delete()
    sweetify.success(request, "Form Successfully Deleted")  
    return redirect('/hutang/')
#HUTANG PEGAWAI
def hutangPeg(request):
    data = HutPegawai.objects.all().order_by('-tanggal')
    oji = Karyawan.objects.get(name='Oji')
    bocil = Karyawan.objects.get(name='Bocil')
    dul = Karyawan.objects.get(name='Dul')
    amin = Karyawan.objects.get(name='Amin')
    anis = Karyawan.objects.get(name='Anis')
    apin = Karyawan.objects.get(name='Apin')
    today = timezone.now().date()
    #Bocil
    hutang_bocil = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=bocil).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_bocil= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=bocil).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_bocil = piutang_bocil - hutang_bocil
    #Oji
    hutang_oji = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=oji).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_oji= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=oji).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_oji = piutang_oji - hutang_oji
    #amin
    hutang_amin = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=amin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_amin= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=amin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_amin = piutang_amin - hutang_amin
    #dul
    hutang_dul = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=dul).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_dul= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=dul).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_dul = piutang_dul - hutang_dul
    #apin
    hutang_apin = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=apin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_apin= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=apin).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_apin = piutang_apin - hutang_apin
    #anis
    hutang_anis = HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='H', pegawai__name=anis).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    piutang_anis= HutPegawai.objects.filter(tanggal__year=today.year, hutang_choice='P',pegawai__name=anis).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    sisa_anis = piutang_anis - hutang_anis
    if request.POST :
        form = HutangPegForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.save()
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/hutangpeg/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    else:
        form = HutangPegForms()
        data = HutPegawai.objects.all().order_by('-tanggal')
    context = {
        'form': form,
        'data':data,
        'bocil':sisa_bocil,
        'anis':sisa_anis,
        'apin':sisa_apin,
        'oji':sisa_oji,
        'dul':sisa_dul,
        'amin':sisa_amin,
        
        "breadcrumb":{"parent":"Hutang Piutang Pegawai","child":"Hutang Pegawai"},
    }
    return render(request, 'hutang_peg/hutang.html', context)

def UpdateHutangPeg(request, pk):
    instance = HutPegawai.objects.get(id=pk)
    if request.POST :
        form = HutangPegForms(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/hutangpeg/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
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
    sweetify.success(request, "Form Successfully Deleted")  
    return redirect('/hutangpeg/')

#TRANSAKSI
@login_required(login_url="/accounts/login/")
def transaksi(request):
    data = Transaksi.objects.all().order_by('-tanggal')
        
    if request.POST :
        excel = ExcelUploadForm(request.POST, request.FILES)
        if excel.is_valid():
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                sweetify.error(request, 'File bukan berformat Excel (.xlsx)')
                return render(request, 'transaksi/index.html', {'excel': excel})

            df = pd.read_excel(excel_file, engine='openpyxl')

            for index, row in df.iterrows():
                try:
                    tanggal = pd.to_datetime(row['tanggal'], format='%Y-%m-%d')
                except ValueError:
                    sweetify.warning(request, f"Format tanggal tidak valid pada baris {index + 2}. Baris diabaikan.")
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
                    sweetify.warning(request, 'Kolom pemasukan atau pengeluaran harus diisi')
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
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/transaksi/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    else:
        form = TransaksiForms()
        excel = ExcelUploadForm()
        data = Transaksi.objects.all().order_by('-tanggal')
    context = {
        'form': form,
        'excel': excel,
        'data':data,
        "breadcrumb":{"parent":"Transaksi","child":"Transaksi"},
    }
    return render(request, 'transaksi/index.html', context)

@login_required(login_url='/accounts/')
def DeleteTr(request, pk):
    Transaksi.objects.get(id=pk).delete()
    sweetify.success(request, "Form Successfully Deleted")  
    return redirect('/transaksi/')

@login_required(login_url='/accounts/')
def UpdateTr(request, pk):
    try :
        data = Transaksi.objects.get(id=pk)
    except Transaksi.DoesNotExist:
        messages.error(request, 'Transaksi not found!', extra_tags="danger")
        return redirect('transaksi')
    form = TransaksiForms(request.POST or None, instance=data)
    if request.POST :
        # form = TransaksiForms(request.POST, instance=formData)
        if form.is_valid():    
            # trform = form.save(commit=False)
            form.owner = request.user
            form.save()
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/transaksi/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    context = {
    'form': form,
    "breadcrumb":{"parent":"Transaksi","child":"Transaksi"},
    }
    return render(request, 'transaksi/index.html', context)

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
                sweetify.error(request, 'File bukan berformat Excel (.xlsx)')
                return render(request, 'transaksi/index.html', {'excel': form})

            df = pd.read_excel(excel_file, engine='openpyxl')

            for index, row in df.iterrows():
                try:
                    tanggal = pd.to_datetime(row['tanggal'], format='%Y-%m-%d')
                except ValueError:
                    sweetify.warning(request, f"Format tanggal tidak valid pada baris {index + 2}. Baris diabaikan.")
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
                    sweetify.warning(request, 'Kolom pemasukan atau pengeluaran harus diisi')
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

            sweetify.success(request, 'Data berhasil diimpor.')
            return redirect('transaksi')
    else:
        form = ExcelUploadForm()
    return render(request, 'transaksi/index.html', {'excel': form})

#Chart Line
@login_required(login_url="/accounts/login/")
def AnalasisChart(request):
    start_date = datetime.now() - timedelta(days=365)
    categories = Kategori.objects.all()
    data = []
    for kategori in categories:
        total_amount = Transaksi.objects.filter(kategori=kategori).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
        data.append({'kategori': kategori.nama, 'jumlah': float(total_amount)})

    labels_don = [item['kategori'] for item in data]
    values_don = [float(item['jumlah']) for item in data]
    daily_data = Transaksi.objects.values('tanggal__date', 'transaksi_choice').annotate(total_jumlah=Sum('jumlah'))

    labels = list(set(entry['tanggal__date'] for entry in daily_data))
    labels.sort()  # Sort the dates chronologically


    return JsonResponse(data={
        'labels_don': labels_don, 
        'values_don': values_don, 
        'labels': labels,
        })
#chart donut
@login_required(login_url="/accounts/login/")
def chart_data(request):
    daily_data = Transaksi.objects.values('tanggal__date', 'transaksi_choice').annotate(total_jumlah=Sum('jumlah'))

    labels = list(set(entry['tanggal__date'] for entry in daily_data))
    labels.sort()  # Sort the dates chronologically
    income_values = [0] * len(labels)
    expense_values = [0] * len(labels)

    for entry in daily_data:
        date_index = labels.index(entry['tanggal__date'])
        if entry['transaksi_choice'] == 'P':
            income_values[date_index] = float(entry['total_jumlah'])
        elif entry['transaksi_choice'] == 'L':
            expense_values[date_index] = float(entry['total_jumlah'])
    return JsonResponse(data={
        'labels': labels,
        'income_values': income_values,
        'expense_values': expense_values,
        })
from zeta import settings
import os
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
            sweetify.success(request, "Formulir Berhasil Dibuat")
            return redirect('/tabungan/')
        else:
            print(form.errors)
            sweetify.error(request, 'Formulir tidak valid.')
            sweetify.error(request, form.errors)
    else:
        form = TabunganForms()
        data = Tabungan.objects.all().order_by('-date','-id')
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Tabungan","child":"Transaksi"},
    }
    return render(request, 'tabungan/tabung.html', context)
