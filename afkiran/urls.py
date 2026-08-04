from django.urls import path
from . import views

app_name = 'afkiran'

urlpatterns = [
    path('', views.afkiran_list, name='afkiran_list'),
    path('create/<int:sale_id>/', views.afkiran_create, name='afkiran_create'),
    path('<int:afkiran_id>/', views.afkiran_detail, name='afkiran_detail'),
    path('<int:afkiran_id>/settle/', views.afkiran_settle, name='afkiran_settle'),
    path('<int:afkiran_id>/recipe/', views.ViewPDF.as_view(), name='afkiran_recipe'),
]
