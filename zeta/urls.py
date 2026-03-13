from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('zetaapp.urls')),
]

if settings.DEBUG:
    # Ini TIDAK BOLEH digunakan di mode produksi (DEBUG=False)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Untuk statik di Development (jika STATICFILES_DIRS digunakan):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)