from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import date, timedelta
from .models import Gaji, PekerjaanBorongan
from django.shortcuts import render
from datetime import date, timedelta
from .models import Absensi, Pegawai
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.http import HttpResponse
from .forms import PegawaiForm
import io
from reportlab.pdfgen import canvas
from datetime import datetime
# RekapGajian
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
from .models import Pegawai, Gaji, Absensi, PekerjaanBorongan

# # 1️⃣ Menampilkan daftar pegawai
@login_required(login_url='/accounts/login/')
def daftar_pegawai(request):
    pegawai_list = Pegawai.objects.all()
    if request.method == "POST":
        form = PegawaiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pegawai:daftar_pegawai')
    else:
        form = PegawaiForm()
    return render(request, 'pegawai/pegawai/daftar_pegawai.html', {'pegawai_list': pegawai_list,'form': form})

# 2️⃣ Tambah pegawai baru
@login_required(login_url='/accounts/login/')
def edit_pegawai(request, pegawai_id):
    pegawai = get_object_or_404(Pegawai, id=pegawai_id)

    if request.method == "POST":
        form = PegawaiForm(request.POST, instance=pegawai)
        if form.is_valid():
            form.save()
            return redirect('pegawai:daftar_pegawai')  # Refresh halaman setelah update
    else:
        form = PegawaiForm(instance=pegawai)

    return render(request, 'pegawai/pegawai/daftar_pegawai.html', {
        'form': form,
        'pegawai': pegawai,
    })
# 4️⃣ Hapus pegawai
@login_required(login_url='/accounts/login/')
def hapus_pegawai(request, pegawai_id):
    pegawai = get_object_or_404(Pegawai, id=pegawai_id)
    if request.method == "POST":
        pegawai.delete()
        return redirect('daftar_pegawai')
    return render(request, 'pegawai/pegawai/hapus_pegawai.html', {'pegawai': pegawai})

# 5️⃣ Detail pegawai
@login_required(login_url='/accounts/login/')
def detail_pegawai(request, pegawai_id):
    pegawai = get_object_or_404(Pegawai, id=pegawai_id)
    return render(request, 'pegawai/pegawai/detail_pegawai.html', {'pegawai': pegawai})

def absensi(request):
    absensi_list = Absensi.objects.all()
    if request.method == "POST":
        form = AbsensiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("pegawai:absensi")
    else:
        form = AbsensiForm()
    return render(request, 'pegawai/gaji/absensi.html', {'absensi_list': absensi_list,'form': form})
def absensi_update(request, pk):
    absensi = get_object_or_404(Absensi, pk=pk)
    if request.method == "POST":
        form = AbsensiForm(request.POST, instance=absensi)
        if form.is_valid():
            form.save()
            return redirect("absensi_list")
    else:
        form = AbsensiForm(instance=absensi)
    return render(request, "absensi_form.html", {"form": form})

def absensi_delete(request, pk):
    absensi = get_object_or_404(Absensi, pk=pk)
    if request.method == "POST":
        absensi.delete()
        return redirect("absensi_list")
    return render(request, "absensi_confirm_delete.html", {"absensi": absensi})


def rekap_absensi_view(request):
    form = FilterAbsensiForm(request.GET or None)  # Form filter tanggal
    today = date.today()
    minggu_mulai = today - timedelta(days=today.weekday())  # Senin
    minggu_selesai = minggu_mulai + timedelta(days=5)  # Sabtu

    pegawai_list = Pegawai.objects.all()

    rekapitulasi = []
    for pegawai in pegawai_list:
        total_hadir = Absensi.total_hadir(pegawai, minggu_mulai, minggu_selesai)
        rekapitulasi.append({
            'pegawai': pegawai,
            'total_hadir': total_hadir,
        })

    absensi_data = {}
    tanggal_mulai = None

    if form.is_valid():
        tanggal_mulai = form.cleaned_data['tanggal_mulai']
        tanggal_selesai = tanggal_mulai + timedelta(days=6)  # Ambil 1 minggu

        # Ambil data absensi dalam rentang tanggal
        absensi_list = Absensi.objects.filter(tanggal__range=[tanggal_mulai, tanggal_selesai]).order_by('tanggal')

        # Mengelompokkan absensi berdasarkan minggu
        for absensi in absensi_list:
            minggu = absensi.tanggal.strftime("%Y-%m-%d")  # Key untuk collapse
            if minggu not in absensi_data:
                absensi_data[minggu] = []
            absensi_data[minggu].append(absensi)
    context = {
        'rekapitulasi': rekapitulasi,
        'minggu_mulai': minggu_mulai,
        'minggu_selesai': minggu_selesai,
        'form': form,
        'absensi_data': absensi_data,
        'tanggal_mulai': tanggal_mulai
    }
    return render(request, 'pegawai/gaji/rekap_absensi.html', context)

def rekap_gaji(request):
    # Mendapatkan periode minggu ini
    today = now().date()
    minggu_mulai = today - timedelta(days=today.weekday())  # Senin minggu ini
    minggu_selesai = minggu_mulai + timedelta(days=6)  # Minggu minggu ini

    # Pegawai harian
    pegawai_harian = Pegawai.objects.filter(posisi="Harian")
    gaji_harian_list = []
    for pegawai in pegawai_harian:
        total_hadir = Absensi.objects.filter(
            pegawai=pegawai, 
            tanggal__range=[minggu_mulai, minggu_selesai], 
            status="Hadir"
        ).count()
        total_gaji = total_hadir * pegawai.gaji_harian
        gaji_harian_list.append({
            "pegawai": pegawai,
            "total_hadir": total_hadir,
            "total_gaji": total_gaji,
        })

    # Pegawai borongan
    pegawai_borongan = Pegawai.objects.filter(posisi="Borongan")
    gaji_borongan_list = []
    for pegawai in pegawai_borongan:
        pekerjaan = PekerjaanBorongan.objects.filter(
            pegawai=pegawai, 
            minggu_mulai=minggu_mulai
        ).first()
        if pekerjaan:
            gaji_borongan_list.append({
                "pegawai": pegawai,
                "total_kg": pekerjaan.total_kg,
                "harga_per_kg": pekerjaan.harga_per_kg,
                "total_gaji": pekerjaan.total_gaji,
            })

    context = {
        "minggu_mulai": minggu_mulai,
        "minggu_selesai": minggu_selesai,
        "gaji_harian_list": gaji_harian_list,
        "gaji_borongan_list": gaji_borongan_list,
    }

    return render(request, "pegawai/gaji/rekap_gaji.html", context)

# ✅ Gaji Mingguan
def gaji_list(request):
    gaji = Gaji.objects.all()
    return render(request, "gaji_list.html", {"gaji": gaji})

def gaji_create(request):
    if request.method == "POST":
        form = GajiForm(request.POST)
        if form.is_valid():
            gaji = form.save(commit=False)
            gaji.save()  # Menghitung total_hadir & total_gaji otomatis
            return redirect("gaji_list")
    else:
        form = GajiForm()
    return render(request, "gaji_form.html", {"form": form})

def gaji_update(request, pk):
    gaji = get_object_or_404(Gaji, pk=pk)
    if request.method == "POST":
        form = GajiForm(request.POST, instance=gaji)
        if form.is_valid():
            form.save()
            return redirect("gaji_list")
    else:
        form = GajiForm(instance=gaji)
    return render(request, "gaji_form.html", {"form": form})

def gaji_delete(request, pk):
    gaji = get_object_or_404(Gaji, pk=pk)
    if request.method == "POST":
        gaji.delete()
        return redirect("gaji_list")
    return render(request, "gaji_confirm_delete.html", {"gaji": gaji})
# ✅ Gaji Borongan
def gaji_borongan_list(request):
    gaji_borongan = GajiBorongan.objects.all()
    return render(request, "gaji_borongan_list.html", {"gaji_borongan": gaji_borongan})

def gaji_borongan_create(request):
    if request.method == "POST":
        form = GajiBoronganForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("gaji_borongan_list")
    else:
        form = GajiBoronganForm()
    return render(request, "gaji_borongan_form.html", {"form": form})

def gaji_borongan_update(request, pk):
    gaji_borongan = get_object_or_404(GajiBorongan, pk=pk)
    if request.method == "POST":
        form = GajiBoronganForm(request.POST, instance=gaji_borongan)
        if form.is_valid():
            form.save()
            return redirect("gaji_borongan_list")
    else:
        form = GajiBoronganForm(instance=gaji_borongan)
    return render(request, "gaji_borongan_form.html", {"form": form})

def gaji_borongan_delete(request, pk):
    gaji_borongan = get_object_or_404(GajiBorongan, pk=pk)
    if request.method == "POST":
        gaji_borongan.delete()
        return redirect("gaji_borongan_list")
    return render(request, "gaji_borongan_confirm_delete.html", {"gaji_borongan": gaji_borongan})


def generate_slip_gaji(request, gaji_id):
    gaji = get_object_or_404(Gaji, id=gaji_id)
    pegawai = gaji.pegawai  # Ambil data pegawai

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Slip_Gaji_{pegawai.nama}.pdf"'

    # Buat canvas PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header Slip Gaji
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Slip Gaji Pegawai")

    # Informasi Pegawai
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Nama Pegawai: {pegawai.nama}")
    p.drawString(50, height - 120, f"Posisi: {pegawai.get_posisi_display()}")

    if pegawai.posisi == "Harian":
        # Menggunakan total_hadir langsung dari model Gaji
        total_gaji = gaji.total_hadir * pegawai.gaji_harian  # Hitung total gaji harian

        p.drawString(50, height - 170, f"Total Kehadiran: {gaji.total_hadir} hari")
        p.drawString(50, height - 190, f"Gaji per Hari: Rp {pegawai.gaji_harian:,.2f}")
        p.drawString(50, height - 210, f"Total Gaji: Rp {total_gaji:,.2f}")

    elif pegawai.posisi == "Borongan":
        # Cek apakah ada pekerjaan borongan terkait gaji ini
        pekerjaan = PekerjaanBorongan.objects.filter(pegawai=pegawai).first()

        if pekerjaan:
            p.drawString(50, height - 170, f"Total Berat: {pekerjaan.total_kg} kg")
            p.drawString(50, height - 190, f"Harga per kg: Rp {pekerjaan.harga_per_kg:,.2f}")
            p.drawString(50, height - 210, f"Total Gaji: Rp {pekerjaan.total_gaji:,.2f}")
        else:
            p.drawString(50, height - 170, "Belum ada pekerjaan borongan.")

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, height - 250, f"Dicetak pada: {date.today()}")

    p.showPage()
    p.save()
    return response