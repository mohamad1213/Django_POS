from django.apps import AppConfig


class PegawaiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pegawai'
    
    def ready(self):
        import pegawai.signals  

