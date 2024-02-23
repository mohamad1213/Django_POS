from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.http.response import HttpResponseRedirect
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import openpyxl
from django.http import HttpResponse
from django.shortcuts import render
from .models import *
from .forms import *
from django.contrib import messages
import locale
from datetime import datetime, timedelta
from django.utils import translation
from babel.numbers import format_currency
# Set the locale to Indonesian (ID) format
locale.setlocale(locale.LC_ALL, 'id_ID')
from django.db.models import Q 
from django.template.loader import get_template
from django.shortcuts import render
from reportlab.pdfgen import canvas
from .forms import ExcelUploadForm
from io import BytesIO
# dashboard pages
from django.http import Http404
from xhtml2pdf import pisa
from django.db.models import Sum
from django.utils import timezone
import pandas as pd
from openpyxl import load_workbook
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from .models import *
from io import BytesIO
from django.views import View
from django.template.loader import render_to_string
def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None
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

class ViewPDF(View):
	def get(self, request, *args, **kwargs):

		pdf = render_to_pdf('generatepdf.html', data)
		return HttpResponse(pdf, content_type='application/pdf')


#Automaticly downloads to PDF file
class DownloadPDF(View):
	def get(self, request, *args, **kwargs):
		
		pdf = render_to_pdf('generatepdf.html', data)

		response = HttpResponse(pdf, content_type='application/pdf')
		filename = "Invoice_%s.pdf" %("12341231")
		content = "attachment; filename='%s'" %(filename)
		response['Content-Disposition'] = content
		return response


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
from django.db.models.functions import TruncDate
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

# @login_required(login_url="/login")
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


# @login_required(login_url="/login")
def pos(request):
    data = Tabungan.objects.all().order_by('-date')
    if request.POST :
        form = TabunganForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.save()
            messages.success(request, "Form Created Successfully")
            return redirect('/pos/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
            messages.error(request, form.errors)
    else:
        form = TabunganForms()
        data = Tabungan.objects.all().order_by('-date','-id')
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Tabungan","child":"Transaksi"},
    }
    return render(request, 'POS/index.html', context)

# @login_required(login_url="/login")
def tabungan(request):
    data = Tabungan.objects.all().order_by('-date')
    if request.POST :
        form = TabunganForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.save()
            messages.success(request, "Form Created Successfully")
            return redirect('/tabungan/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
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

# @login_required(login_url="/login")
def profit(request):
    data = Profito.objects.all().order_by('-date')
    if request.POST :
        form = ProfitForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.owner = request.user
            trform.save()
            messages.success(request, "Form Created Successfully")
            return redirect('/profit/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
            messages.error(request, form.errors)
    else:
        form = ProfitForms()
        data = Profito.objects.all().order_by('-date','-id')
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Profit","child":"Transaksi"},
    }
    return render(request, 'profit/profit.html', context)

# @login_required(login_url="/login")
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
            messages.success(request, "Form Created Successfully")
            return redirect('/hutang/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
            messages.error(request, form.errors)
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

def hutangPeg(request):
    data = HutPegawai.objects.all().order_by('-tanggal')
    if request.POST :
        form = HutangPegForms(request.POST)
        if form.is_valid():    
            trform = form.save(commit=False)
            trform.save()
            messages.success(request, "Form Created Successfully")
            return redirect('/hutangpeg/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
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

# @login_required(login_url='/accounts/')
def DeleteHutang(request, pk):
    HutangPiutang.objects.get(id=pk).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/transaksi/')

# @login_required(login_url="/login")
def transaksi(request):
    data = Transaksi.objects.all().order_by('-tanggal')
        
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
            messages.success(request, "Form Created Successfully")
            return redirect('/transaksi/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
            messages.error(request, form.errors)
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

# @login_required(login_url='/accounts/')
def DeleteTr(request, pk):
    Transaksi.objects.get(id=pk).delete()
    messages.success(request, "Form Successfully Deleted")  
    return redirect('/transaksi/')

# @login_required(login_url='/accounts/')
def UpdateTr(request, pk):
    get_id = get_object_or_404(Transaksi, id=pk)
    form = TransaksiForms(request.POST or None, instance=get_id)
    if request.POST :
        # form = TransaksiForms(request.POST, instance=formData)
        if form.is_valid():    
            # trform = form.save(commit=False)
            # trform.owner = request.user
            form.save()
            messages.success(request, "Form Created Successfully")
            return redirect('/transaksi/')
        else:
            print(form.errors)
            messages.error(request, 'Invalid Form Submission.')
            messages.error(request, form.errors)
    else:
        form = TransaksiForms()
        data = Transaksi.objects.all() 
        context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Transaksi","child":"Transaksi"},
    }
    return render(request, 'transaksi/index.html', context)


#laporan
def laporan(request):
    data = Transaksi.objects.all().order_by('-tanggal','-id')
    
    context = {
        'data': data,
    }

    return render(request, 'laporan/laporan.html', context)

# page layout views

# @login_required(login_url="/login")
def page_layout_boxed(request):
    context ={"layout":"box-layout","breadcrumb":{"parent":"Page Layout","child":"Box Layout"}}
    return render(request,'page_layout/boxed/box-layout.html',context)

# @login_required(login_url="/login")
def page_layout_rtl(request):
    context={"layout":"rtl","breadcrumb":{"parent":"Page Layout","child":"RTL"}}
    return render(request,'page_layout/RTL/layout-rtl.html',context)

# @login_required(login_url="/login")
def page_layout_dark(request):
    context ={"layout":"dark-only","breadcrumb":{"parent":"Page Layout","child":"Layout Dark"}}
    return render(request,'page_layout/dark_layout/layout-dark.html',context)

# @login_required(login_url="/login")
def page_layout_hide_nav_scroll(request):
    context={"breadcrumb":{"parent":"Page Layout","child":"Hide Menu On Scroll"}}
    return render(request,'page_layout/hide_nav_scroll/hide-on-scroll.html',context)

# @login_required(login_url="/login")
def page_layout_footer_light(request):
    context={"breadcrumb":{"parent":"Page Layout","child":"Footer Light"}}
    return render(request,'page_layout/footer_light/footer-light.html',context)

# @login_required(login_url="/login")
def page_layout_footer_dark(request):
    context={"footer":"footer-dark","breadcrumb":{"parent":"Page Layout","child":"Footer Dark"}}
    return render(request,'page_layout/footer_dark/footer-dark.html',context)

# @login_required(login_url="/login")
def page_layout_footer_fixed(request):
    context={"footer":"footer-fix","breadcrumb":{"parent":"Page Layout","child":"Footer Fixed"}}
    return render(request,'page_layout/footer_fixed/footer-fixed.html',context)

# to do views

# @login_required(login_url="/login")
def to_do_view(request):
    context={"breadcrumb":{"parent":"Apps","child":"To Do"}}
    return render(request,'to_do/to-do.html',context)

# @login_required(login_url="/login")
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
    
# @login_required(login_url="/login")
def markAllComplete(request):
    allTasks = Task.objects.all()
    for oneTask in allTasks:
        oneTask.complete = True
        oneTask.save()
    return HttpResponseRedirect("/to_do_database")


# @login_required(login_url="/login")
def markAllIncomplete(request):
    allTasks = Task.objects.all()
    for oneTask in allTasks:
        oneTask.complete = False
        oneTask.save()
    return HttpResponseRedirect("/to_do_database")


# @login_required(login_url="/login")
def deleteTask(request, pk):
    item = Task.objects.get(id=pk)
    
    #if request.method == "POST":
    item.delete()
    return HttpResponseRedirect("/to_do_database")


# @login_required(login_url="/login")
def updateTask(request, pk):
    task = Task.objects.get(id=pk)
    if task.complete == False:
        task.complete = True
        task.save()
    else:
        task.complete = False
        task.save()

    return HttpResponseRedirect("/to_do_database")
