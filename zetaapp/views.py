from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.http.response import HttpResponseRedirect
from .models import *
from .forms import *
from django.contrib import messages
import locale

# Set the locale to Indonesian (ID) format
locale.setlocale(locale.LC_ALL, 'id_ID')


# dashboard pages

from django.utils.translation import activate
from django.db.models import Sum
from django.utils import timezone
# @login_required(login_url="/login")
def indexPage(request):
    data = Transaksi.objects.all().order_by('-tanggal')[:7]
    calculate = Transaksi.objects.filter(transaksi_choice='P')
    for u in calculate :
        calculate = u.calculate_profit_loss
    today = timezone.now().date()
    print(today)
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
        data = Tabungan.objects.all()
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
        data = Profito.objects.all()
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
        data = HutangPiutang.objects.all()
    context = {
        'form': form,
        'data':data,
        "breadcrumb":{"parent":"Hutang Piutang","child":"Transaksi"},
    }
    return render(request, 'hutang/hutang.html', context)

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
        data = Transaksi.objects.all()
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
