from dataclasses import field
from django import forms
from django.forms import ModelForm

from .models import *
# forms.py

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(widget=forms.FileInput(attrs={'name':'excel_file', 'class':'form-control' ,'type':'file'}))
    class Meta:
        model = Transaksi
        exclude = ['owner']
        widgets = {
            'jumlah': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_jumlah',
                'placeholder': 'Rp 0',
            }),
            'tanggal': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.date.value|date:"d-m-Y"}}'}),
            'keterangan': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.keterangan.value}}'})
        }

class TaskForm(forms.ModelForm):
    title = forms.CharField(max_length=200, widget= forms.Textarea(attrs={'placeholder':'Enter new task here. . .'}))

    class Meta:
        model = Task
        fields = '__all__'

class TransaksiForms(ModelForm):
    class Meta:
        model = Transaksi
        exclude = ['owner']
        widgets = {
            'jumlah': forms.TextInput({'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','name':'rupiah','id':"id_jumlah"}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.date.value|date:"d-m-Y"}}'}),
            'keterangan': forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.keterangan.value}}'})
        }
    def __init__(self, *args, **kwargs):
        super(TransaksiForms, self).__init__(*args, **kwargs)
        self.fields['kategori'].empty_label = 'Select item ...'
        self.fields['kategori'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.kategori.value}}'})
        self.fields['transaksi_choice'].empty_label = 'Select item ...'
        self.fields['transaksi_choice'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.transaksi_choice.value}}'})

class HutangForms(ModelForm):
    class Meta:
        model = HutangPiutang
        exclude = ['owner']
        widgets = {
            'jumlah': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.jumlah.value}}'}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.date.value|date:"d-m-Y"}}'}),
            'keterangan': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.keterangan.value}}'})
        }
    def __init__(self, *args, **kwargs):
        super(HutangForms, self).__init__(*args, **kwargs)
        self.fields['hutang_choice'].empty_label = 'Select item ...'
        self.fields['hutang_choice'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.hutang.value}}'})

class HutangPegForms(ModelForm):
    class Meta:
        model = HutPegawai
        fields = ['jumlah', 'tanggal','keterangan','pegawai','hutang_choice']
        widgets = {
            'jumlah': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.jumlah.value}}'}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.date.value|date:"d-m-Y"}}'}),
            'keterangan': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.keterangan.value}}'})
        }
    def __init__(self, *args, **kwargs):
        super(HutangPegForms, self).__init__(*args, **kwargs)
        self.fields['pegawai'].empty_label = 'Select item ...'
        self.fields['pegawai'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.hutang.value}}'})
        self.fields['hutang_choice'].empty_label = 'Select item ...'
        self.fields['hutang_choice'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.hutang.value}}'})


class ProfitForms(ModelForm):
    class Meta:
        model = Profito2
        fields = '__all__'
        widgets = {
            'tanggal': forms.DateInput(attrs={
                'type':'date',
                'class':'form-control'
            }),
            'nama_barang': forms.TextInput(attrs={'class':'form-control'}),
            'harga_beli': forms.TextInput(attrs={'class':'form-control', 'id':'id_harga_beli', 'placeholder':'Rp 0'}),
            'harga_jual': forms.TextInput(attrs={'class':'form-control', 'id':'id_harga_jual', 'placeholder':'Rp 0'}),
            'solar': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_solar', 'placeholder':'Rp 0'}),
            'karung': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_karung', 'placeholder':'Rp 0'}),
            'ongkos_kirim': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_ongkos_kirim', 'placeholder':'Rp 0'}),
            'ongkos_muat': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_ongkos_muat', 'placeholder':'Rp 0'}),
            'ongkos_lain': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_ongkos_lain', 'placeholder':'Rp 0'}),
            'ongkos_sortir': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_ongkos_sortir', 'placeholder':'Rp 0'}),
            'ongkos_giling': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_ongkos_giling', 'placeholder':'Rp 0'}),
            'biaya_darurat_mesin': forms.TextInput(attrs={'class':'form-control biaya', 'id':'id_biaya_darurat_mesin', 'placeholder':'Rp 0'}),
            'keterangan': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
        }
class Profit2Forms(ModelForm):
    class Meta:
        model = Profito
        exclude = ['owner']
        widgets = {
            'jumlah_brg': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da', 'placeholder':"Kg", 'name':'jumlah_brg'}),
            'nama_suplayer': forms.TextInput({'class': 'form-control', 'type':'text', 'style':'padding:6px 10px ;border: 1px solid #ced4da','name':'nama_suplayer'}),
            'harga_jual': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da','name':'harga_jual'}),
            'harga_beli': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da','name':'harga_beli'}),
            'date': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','name':'date'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','name':'description'})
        }
class TabunganForms(ModelForm):
    class Meta:
        model = Tabungan
        exclude = []
        widgets = {
            'nominal': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.jumlah.value}}'}),
            'date': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.date.value|date:"d-m-Y"}}'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.keterangan.value}}'})
        }
    def __init__(self, *args, **kwargs):
        super(TabunganForms, self).__init__(*args, **kwargs)
        self.fields['transaksi_choice'].empty_label = 'Select item ...'
        self.fields['transaksi_choice'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.hutang.value}}'})


