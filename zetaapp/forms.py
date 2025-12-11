from dataclasses import field
from django import forms
from django.forms import ModelForm
from django.forms import modelformset_factory
from .models import *
# forms.py
class StockInForm(forms.ModelForm):
    class Meta:
        model = StockIn
        fields = ["product", "quantity", "reference","note" ]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control form-control-sm",
            }),
            "reference ": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "note ": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        }

    def clean_quantity(self):
        q = self.cleaned_data.get("quantity")
        if q is None:
            raise forms.ValidationError("Quantity wajib diisi.")
        if q <= 0:
            raise forms.ValidationError("Quantity harus lebih dari 0.")
        return q
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
            'jumlah': forms.TextInput({'class': 'form-control rupiah','style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'keterangan': forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da'})
        }
    def __init__(self, *args, **kwargs):
        super(TransaksiForms, self).__init__(*args, **kwargs)
        self.fields['kategori'].empty_label = 'Select item ...'
        self.fields['kategori'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da'})
        self.fields['transaksi_choice'].empty_label = 'Select item ...'
        self.fields['transaksi_choice'].widget.attrs.update({ 'class': 'form-control','style':'padding:6px 10px ;border: 1px solid #ced4da'})

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


class ProfitForms(forms.ModelForm):
    class Meta:
        model = Profito2
        fields = [
            'nama_barang',
            'berat_input',
            'harga_beli_per_kg',
            'harga_jual_per_kg',
            'tabungan_persen',
            'solar',
            'karung',
            'ongkos_kirim',
            'ongkos_sortir',
            'ongkos_giling',
            'ongkos_muat',
            'susutan_persen',
        ]
        widgets = {
            'nama_barang': forms.TextInput(attrs={'class': 'form-control'}),
            'berat_input': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'harga_beli_per_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'harga_jual_per_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'solar': forms.NumberInput(attrs={'class': 'form-control'}),
            'karung': forms.NumberInput(attrs={'class': 'form-control'}),
            'ongkos_kirim': forms.NumberInput(attrs={'class': 'form-control'}),
            'ongkos_sortir': forms.NumberInput(attrs={'class': 'form-control'}),
            'ongkos_giling': forms.NumberInput(attrs={'class': 'form-control'}),
            'ongkos_muat': forms.NumberInput(attrs={'class': 'form-control'}),
            'susutan_persen': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'nama_barang': 'Nama Barang',
            'berat_input': 'Berat Masuk (kg)',
            'harga_beli_per_kg': 'Harga Beli per kg',
            'harga_jual_per_kg': 'Harga Jual per kg',
            'solar': 'Biaya Solar per kg',
            'karung': 'Biaya Karung per kg',
            'ongkos_kirim': 'Ongkos Kirim per kg',
            'ongkos_sortir': 'Biaya Sortir per kg',
            'ongkos_giling': 'Biaya Giling per kg',
            'ongkos_muat': 'Biaya Muat per kg',
            'susutan_persen': 'Susutan (%)',
        }
class ItemForm(forms.ModelForm):
    class Meta:
        model = Profito2
        # Hanya field yang diinput per baris
        fields = [
            'nama_barang',
            'berat_input',
            'harga_beli_per_kg',
            'harga_jual_per_kg',
        ]
        widgets = {
             'nama_barang': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
             'berat_input': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
             'harga_beli_per_kg': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
             'harga_jual_per_kg': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
         }
        labels = {
            'nama_barang': 'Nama Barang',
            'berat_input': 'Berat Masuk (kg)',
            'harga_beli_per_kg': 'Harga Beli/kg',
            'harga_jual_per_kg': 'Harga Jual/kg',
        }

# Definisikan Formset untuk item
ItemFormSet = modelformset_factory(
    Profito2,
    form=ItemForm,
    extra=5,
    can_delete=True,
)
# --- 2. Form untuk Biaya Global (GlobalCostForm) ---
class GlobalCostForm(forms.ModelForm):
    class Meta:
        model = Profito2
        # Hanya field biaya global yang diinput user
        fields = [
            'solar',
            'karung',
            'ongkos_kirim',
            'ongkos_sortir',
            'ongkos_giling',
            'ongkos_muat',
            'susutan_persen',
            'tabungan_persen',
        ]
        widgets = {
             'solar': forms.NumberInput(attrs={'class': 'form-control'}),
             'karung': forms.NumberInput(attrs={'class': 'form-control'}),
             'ongkos_kirim': forms.NumberInput(attrs={'class': 'form-control'}),
             'ongkos_sortir': forms.NumberInput(attrs={'class': 'form-control'}),
             'ongkos_giling': forms.NumberInput(attrs={'class': 'form-control'}),
             'ongkos_muat': forms.NumberInput(attrs={'class': 'form-control'}),
             'susutan_persen': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'tabungan_persen': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
         }
        labels = {
            'solar': 'Biaya Solar/kg',
            'karung': 'Biaya Karung/kg',
            'ongkos_kirim': 'Ongkos Kirim/kg',
            'ongkos_sortir': 'Biaya Sortir/kg',
            'ongkos_giling': 'Biaya Giling/kg',
            'ongkos_muat': 'Biaya Muat/kg',
            'susutan_persen': 'Susutan (%)',
            'tabungan_persen': 'Tabungan (%)',
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


