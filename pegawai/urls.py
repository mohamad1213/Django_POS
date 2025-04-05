from django.urls import path

from . import views

app_name = "pegawai"
urlpatterns = [
     path('', views.daftar_pegawai, name='daftar_pegawai'),
     path('edit/<int:pegawai_id>/', views.edit_pegawai, name='edit_pegawai'),
     path('hapus/<int:pegawai_id>/', views.hapus_pegawai, name='hapus_pegawai'),
     path('detail/<int:pegawai_id>/', views.detail_pegawai, name='detail_pegawai'),
     path('absensi/', views.absensi, name='absensi'),
     path('rekap_absensi/', views.rekap_absensi_view, name='rekap_absensi'),
     path('rekap_gaji/', views.rekap_gaji, name='rekap_gaji'),
     path('slip-gaji/<int:gaji_id>/', views.generate_slip_gaji, name='generate_slip_gaji'),
     # path('gaji/', views.daftar_gaji, name='daftar_gaji'),
     # path('gaji/hitung/', views.hitung_gaji, name='hitung_gaji'),
     # path('gaji/approve/<int:gaji_id>/', views.approve_gaji, name='approve_gaji'),
]
