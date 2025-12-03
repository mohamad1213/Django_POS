from django.db import models
from datetime import date
class Pegawai(models.Model):
    STATUS_POSISI = [
        ('Borongan', 'Borongan'),
        ('Harian', 'Harian'),
    ]
    nama = models.CharField(max_length=255)
    posisi = models.CharField(max_length=10, choices=STATUS_POSISI)
    tanggal_masuk = models.DateField()
    status = models.CharField(max_length=50, choices=[('Aktif', 'Aktif'), ('Resign', 'Resign')])
    gaji_harian = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.nama
class PekerjaanBorongan(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, limit_choices_to={'posisi': 'Borongan'})
    minggu_mulai = models.DateField(default=date.today)
    minggu_selesai = models.DateField()
    total_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Total berat yang dikerjakan
    harga_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Harga borongan per kg
    total_gaji = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_gaji = self.total_kg * self.harga_per_kg
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pegawai.nama} - {self.minggu_mulai} s/d {self.minggu_selesai}"

class Absensi(models.Model):
    STATUS_ABSENSI = [
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa')
    ]

    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE)
    tanggal = models.DateField()
    jam_masuk = models.TimeField(null=True, blank=True)
    jam_keluar = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_ABSENSI,
        default='Hadir'
    )
    
    def __str__(self):
        return f"{self.pegawai.nama} - {self.tanggal}"
    
    def save(self, *args, **kwargs):
        # Jika tidak ada jam masuk, set otomatis ke Alpa
        if not self.jam_masuk and self.status == 'Hadir':
            self.status = 'Alpa'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pegawai.nama} - {self.tanggal}"

    @classmethod
    def total_hadir(cls, pegawai, minggu_mulai, minggu_selesai):
        return cls.objects.filter(
            pegawai=pegawai,
            tanggal__range=[minggu_mulai, minggu_selesai],
            status='Hadir'
        ).count()
class Gaji(models.Model):
    STATUS_GAJI = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
    ]

    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE)
    minggu_mulai = models.DateField(default=date.today)
    minggu_selesai = models.DateField()
    total_hadir = models.IntegerField(default=0, editable=False)
    total_gaji = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_GAJI, default='Pending')

    def save(self, *args, **kwargs):
        # Hitung jumlah kehadiran dalam seminggu
        self.total_hadir = Absensi.objects.filter(
            pegawai=self.pegawai,
            tanggal__range=[self.minggu_mulai, self.minggu_selesai],
            status='Hadir'
        ).count()

        # Hitung total gaji
        self.total_gaji = self.total_hadir * self.pegawai.gaji_harian

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pegawai.nama} - {self.minggu_mulai} s/d {self.minggu_selesai}"
    
class GajiBorongan(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, limit_choices_to={'posisi': 'Borongan'})
    minggu_mulai = models.DateField(default=date.today)
    minggu_selesai = models.DateField()
    total_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Total barang dalam kg
    harga_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Harga borongan per kg
    total_gaji = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved')],
        default='Pending'
    )

    def save(self, *args, **kwargs):
        self.total_gaji = self.total_kg * self.harga_per_kg
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pegawai.nama} - {self.minggu_mulai} s/d {self.minggu_selesai}"
