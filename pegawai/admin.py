from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Pegawai)
admin.site.register(Gaji)
admin.site.register(GajiBorongan)
admin.site.register(PekerjaanBorongan)