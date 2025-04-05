from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
# from .models import Gaji
from zetaapp.models import Transaksi

# @receiver(post_save, sender=Gaji)
# def buat_transaksi_setelah_approval(sender, instance, **kwargs):
#     if instance.status == 'Approved':  
#         Transaksi.objects.create(
#             owner=instance.pegawai,  # Jika Pegawai tidak terkait User, ubah ini
#             jumlah=instance.total_gaji,
#             tanggal=now().date(),
#             transaksi_choice='L',  # Pengeluaran
#             keterangan=f"Gaji bulan {instance.bulan} {instance.tahun} untuk {instance.pegawai.nama}"
#         )
