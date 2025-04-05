from django import forms
from .models import *

from django import forms
from .models import Pegawai
from django import forms
from .models import Absensi
class FilterAbsensiForm(forms.Form):
    tanggal_mulai = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Pilih Tanggal Awal Minggu"
    )
class PekerjaanBoronganForm(forms.ModelForm):
    class Meta:
        model = PekerjaanBorongan
        fields = ['pegawai', 'minggu_mulai', 'minggu_selesai', 'total_kg', 'harga_per_kg']
        widgets = {
            'minggu_mulai': forms.DateInput(attrs={'type': 'date'}),
            'minggu_selesai': forms.DateInput(attrs={'type': 'date'}),
        }
class AbsensiForm(forms.ModelForm):
    class Meta:
        model = Absensi
        fields = ['pegawai', 'tanggal', 'jam_masuk', 'jam_keluar', 'status']
        widgets = {
            'pegawai': forms.Select(attrs={'class': 'form-control'}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'jam_masuk': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'jam_keluar': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
class GajiForm(forms.ModelForm):
    class Meta:
        model = Gaji
        fields = ['pegawai', 'minggu_mulai', 'minggu_selesai', 'status']
        widgets = {
            'pegawai': forms.Select(attrs={'class': 'form-control'}),
            'minggu_mulai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'minggu_selesai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# ✅ Form Gaji Borongan
class GajiBoronganForm(forms.ModelForm):
    class Meta:
        model = GajiBorongan
        fields = ['pegawai', 'minggu_mulai', 'minggu_selesai', 'total_kg', 'harga_per_kg', 'status']
        widgets = {
            'pegawai': forms.Select(attrs={'class': 'form-select'}),
            'minggu_mulai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'minggu_selesai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Kg'}),
            'harga_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Harga per Kg'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
class PegawaiForm(forms.ModelForm):
    class Meta:
        model = Pegawai
        fields = ['nama', 'posisi', 'tanggal_masuk', 'status', 'gaji_harian']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'posisi': forms.Select(attrs={'class': 'form-control'}),
            'tanggal_masuk': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'gaji_harian': forms.NumberInput(attrs={'class': 'form-control'}),
        }
