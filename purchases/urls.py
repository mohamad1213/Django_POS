from django.urls import path
from . import views

app_name = "purchases"

urlpatterns = [
    path('', views.purchase_list_view, name='purchase_list'),
    path('add/', views.purchase_add_view, name='purchase_add'),
    path('details/<int:purchase_id>/', views.purchase_details_view, name='purchase_details'),
    path('delete/<int:purchase_id>/', views.delete_purchase, name='delete_purchase'),
    path('pdf/<int:purchase_id>/', views.ViewPDF.as_view(), name='purchase_receipt_pdf'),
]
