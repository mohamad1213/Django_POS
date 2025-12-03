from dataclasses import field
from django import forms
from django.forms import ModelForm

from .models import *
class CategoriesForm(ModelForm):
    class Meta:
        model = Category
        exclude = []
        widgets = {
            'status': forms.Select({'class': 'form-control', 'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'name': forms.TextInput(attrs={'class': 'form-control' ,'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da'})
        }
class ProductForm(ModelForm):
    class Meta:
        model = Product
        exclude = []
        widgets = {
            'status': forms.Select({'class': 'form-control', 'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'name': forms.TextInput(attrs={'class': 'form-control' ,'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'category': forms.Select(attrs={'class': 'form-control' ,'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'price': forms.NumberInput(attrs={'class': 'form-control' ,'style':'padding:6px 10px ;border: 1px solid #ced4da'}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control' , 'type':'text','style':'padding:6px 10px ;border: 1px solid #ced4da'})
        }