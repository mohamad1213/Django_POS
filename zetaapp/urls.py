from django.urls import path
from . import views
urlpatterns = [

    # dashboard paths

    path('', views.indexPage,name='dashboard'),
    # Transaksi
    path('transaksi/', views.transaksi,name='transaksi'),
    path('transaksi/<pk>/update/', views.UpdateTr,name='updatetr'),
    path('transaksi/<pk>/delete/', views.DeleteTr,name='deletetr'),

    # HutangPiutang
    path('hutang/', views.hutang,name='hutang'),
    path('transaksi/<pk>/update/', views.UpdateTr,name='updatetr'),
    path('transaksi/<pk>/delete/', views.DeleteTr,name='deletetr'),

    #Tabungan
    path('tabungan/', views.tabungan,name='tabungan'),

    #profit
    path('profit/', views.profit,name='profit'),

    # page layout paths

    path('page_layout_boxed',views.page_layout_boxed,name='page_layout_boxed'),
    path('page_layout_rtl',views.page_layout_rtl,name='page_layout_rtl'),
    path('page_layout_dark',views.page_layout_dark,name='page_layout_dark'),
    path('page_layout_hide_nav_scroll',views.page_layout_hide_nav_scroll,name='page_layout_hide_nav_scroll'),
    path('page_layout_footer_light',views.page_layout_footer_light,name='page_layout_footer_light'),
    path('page_layout_footer_dark',views.page_layout_footer_dark,name='page_layout_footer_dark'),
    path('page_layout_footer_fixed',views.page_layout_footer_fixed,name='page_layout_footer_fixed'),


]