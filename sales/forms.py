from django import forms

class ReceiptUploadForm(forms.Form):

    image = forms.ImageField(
        label="Upload Nota"
    )