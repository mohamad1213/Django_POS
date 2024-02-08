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
def import_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)
            print(df)
            print(df['kategori_id'])
            if 'pemasukan' in df.columns:
                for index, row in df.iterrows():
                    kategori_id = row['kategori_id']
                    try:
                        kategori_instance = Kategori.objects.get(nama=kategori_id)
                    except Http404:
                        print(f"Kategori with id {kategori_id} does not exist. Skipping row {index + 2}.")
                        continue
                    Transaksi.objects.create(
                        owner=request.user,
                        jumlah=row['pemasukan'],
                        tanggal=row['tanggal'],
                        keterangan=row['keterangan'],
                        transaksi_choice='P',  # Pemasukan
                        kategori_id=kategori_instance,
                    )
            else:
                print("Column 'pemasukan' not found in DataFrame")
                # Check if pengeluaran column is not NaN
            if 'pengeluaran' in df.columns:
                for index, row in df.iterrows():
                    kategori_id = row['kategori_id']
                    try:
                        kategori_instance = Transaksi.objects.get(kategori=kategori_id)
                    except Http404:
                        print(f"Kategori with id {kategori_id} does not exist. Skipping row {index + 2}.")
                        continue
                    Transaksi.objects.create(
                        owner=request.user,
                        jumlah=row['pengeluaran'],
                        tanggal=row['tanggal'],
                        keterangan=row['keterangan'],
                        transaksi_choice='L', # Pengeluaran
                        kategori_id=kategori_instance,
                    )
                messages.success(request, 'mantaops.')
            else:
                print("Column 'pemasukan' not found in DataFrame")
            return redirect('/')  # Redirect to a success page
    else:
        form = ExcelUploadForm()

    return render(request, 'transaksi/import_excel.html', {'form': form})


def generate_pdf(request):
    data = Transaksi.objects.all().order_by('-tanggal','-id')
    context_data = {
        'data': data,
    }
            

    # Render the HTML template with the invoice data
    template = get_template('generatepdf.html')
    html = template.render(context_data)

    # Create a BytesIO buffer to write the PDF content
    pdf_buffer = BytesIO()

    # Use xhtml2pdf to generate the PDF from the HTML content
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

    if pisa_status.err:
        return HttpResponse('Error creating PDF', content_type='text/plain')

    # Set the buffer's file pointer to the beginning
    pdf_buffer.seek(0)

    # Create a response with the PDF content
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'filename=invoice.pdf'

    return response
def generate_chart_data(data, interval):
    chart_data = []

    if interval == 'daily':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'],
                'jumlah': entry['jumlah'],
            })
    elif interval == 'monthly':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'].strftime('%B %Y'),  # Format as Month Year
                'jumlah': entry['jumlah'],
            })
    elif interval == 'yearly':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'].year,
                'jumlah': entry['jumlah'],
            })

    return chart_data
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
    total_pemasukan_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='P').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pengeluaran_harian = Transaksi.objects.filter(tanggal=today, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pengeluaran_bulanan = Transaksi.objects.filter(tanggal__month=today.month, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
    total_pengeluaran_tahunan = Transaksi.objects.filter(tanggal__year=today.year, transaksi_choice='L').aggregate(Sum('jumlah'))['jumlah__sum'] or 0
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
        data = HutangPiutang.objects.all().order_by('-tanggal','-id')
    context = {
        'form': form,
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
        data = Transaksi.objects.all().order_by('-tanggal')
    context = {
        'form': form,
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
# def chart_data(request):
#   # Hitung tanggal awal sesuai dengan periode waktu yang diminta
#     start_date = datetime.now() - timedelta(days=365)
#     categories = Kategori.objects.all()
#     data = []

#     for kategori in categories:
#         total_amount = Transaksi.objects.filter(kategori=kategori).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
#         data.append({'kategori': kategori.nama, 'jumlah': float(total_amount)})

#     labels_don = [item['kategori'] for item in data]
#     values_don = [float(item['jumlah']) for item in data]
#     # Ambil data sesuai dengan periode waktu yang diminta
#     data_pemasukan = Transaksi.objects \
#         .filter(tanggal__gte=start_date, transaksi_choice='P') \
#         .extra({'month': "EXTRACT(month FROM tanggal)"}) \
#         .values('month') \
#         .annotate(jumlah=models.Sum('jumlah')) \
#         .order_by('month')
#     data_pengeluaran = Transaksi.objects \
#         .filter(tanggal__gte=start_date, transaksi_choice='L') \
#         .extra({'month': "EXTRACT(month FROM tanggal)"}) \
#         .values('month') \
#         .annotate(jumlah=models.Sum('jumlah')) \
#         .order_by('month')
#     data_labels= Transaksi.objects \
#         .filter(tanggal__gte=start_date) \
#         .extra({'month': "EXTRACT(month FROM tanggal)"}) \
#         .values('month') \
#         .annotate(jumlah=models.Sum('jumlah')) \
#         .order_by('month')
#     data = Transaksi.objects.values('tanggal').annotate(total_nominal=Sum('jumlah'))
    
#     # Daftar nama bulan untuk label
#     month_names = [
#         "Jan",
#         "Feb",
#         "Mar",
#         "Apr",
#         "May",
#         "Jun",
#         "Jul",
#         "Aug",
#         "Sep",
#         "Oct",
#         "Nov",
#         "Dec",
#     ]
#     # Format tanggal sesuai dengan periode waktu yang diminta
#     labels = [month_names[int(entry['month']) - 1] for entry in data_labels]
#     # values = [entry['jumlah'] for entry in data]
#     dates = [entry['tanggal'] for entry in data]
#     print(dates)
#     values_pemasukan = [entry['jumlah'] if 'jumlah' in entry else 0 for entry in data_pemasukan]
#     values_pengeluaran = [entry['jumlah'] if 'jumlah' in entry else 0 for entry in data_pengeluaran]
#     count = Transaksi.objects.count()
#     print(count)
#     return JsonResponse(data={
#         'labels': labels, 
#         'labels_don': labels_don, 
#         'values_don': values_don, 
#         'dates': dates, 
#         'count': count, 
#         'values_pemasukan': values_pemasukan,
#         'values_pengeluaran': values_pengeluaran
        
#         })
    # income_data = Transaksi.objects.filter(transaksi_choice='P').values('tanggal__date').annotate(total_jumlah=Sum('jumlah'))
    # expense_data = Transaksi.objects.filter(transaksi_choice='L').values('tanggal__date').annotate(total_jumlah=Sum('jumlah'))

    # labels = list(set(entry['tanggal__date'] for entry in income_data))
    # labels.extend(set(entry['tanggal__date'] for entry in expense_data))
    # labels = list(set(labels))
    # labels.sort()  # Sort the dates chronologically
    # print(labels)