from dataclasses import field
from django import forms
from django.forms import ModelForm

from .models import *

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
            'jumlah': forms.NumberInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.jumlah.value}}'}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.date.value|date:"d-m-Y"}}'}),
            'keterangan': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da','value':'{{form.keterangan.value}}'})
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

class ProfitForms(ModelForm):
    class Meta:
        model = Profito
        exclude = ['owner']
        widgets = {
            'jumlah_brg': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da', 'placeholder':"Kg"}),
            'nama_suplayer': forms.TextInput({'class': 'form-control', 'type':'text', 'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'harga_jual': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'harga_beli': forms.TextInput({'class': 'form-control', 'type':'number', 'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'date': forms.DateInput(attrs={'class': 'form-control' , 'type':'date','style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da'})
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


