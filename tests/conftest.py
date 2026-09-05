"""
conftest.py — Konfigurasi pytest untuk Django POS

Cara menjalankan:
  pip install pytest pytest-django
  pytest tests/ -v

Atau tanpa pytest (Django native):
  python manage.py test tests --verbosity=2
"""
import django
from django.conf import settings


def pytest_configure(config):
    """Konfigurasi Django settings untuk pytest."""
    if not settings.configured:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                    'TEST': {
                        'NAME': ':memory:',
                    },
                }
            }
        )
