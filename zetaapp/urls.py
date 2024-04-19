from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

    # dashboard paths

    path('', views.indexPage,name='dashboard'),
    # POS
    path('product/', include('products.urls')),
    path('customer/', include('customers.urls')),
    path('sales/', include('sales.urls')),
    path('accounts/', include('authentication.urls')),
    # Transaksi
    path('transaksi/', views.transaksi,name='transaksi'),
    path('transaksi/<pk>/update/', views.UpdateTr,name='updatetr'),
    path('transaksi/<pk>/delete/', views.DeleteTr,name='deletetr'),

    # HutangPiutang
    path('hutang/', views.hutang,name='hutang'),
    path('hutang/<pk>/delete/', views.DeleteHutang,name='deletehut'),
    path('hutang/<pk>/update/', views.UpdateHutangPeg,name='updatehut'),
    

    # path('chart_data/<str:interval>/', views.chart_data, name='chart_data'),
    path('chart_data/', views.chart_data, name='chart_data'),
    path('analisis_chart/', views.AnalasisChart, name='analsis_chart'),
    path('pdf_view/', views.ViewPDF.as_view(), name="pdf_view"),
    path('pdf_download/', views.DownloadPDF.as_view(), name="pdf_download"),
    path('hutangpeg/', views.hutangPeg, name='hutangpeg'),
    path('hutangpeg/<pk>/delete/', views.DeleteHutangPeg, name='DeleteHutangPeg'),
    #Tabungan
    path('tabungan/', views.tabungan,name='tabungan'),

    #profit
    path('profit/', views.profit,name='profit'),
    path('profit/<pk>/delete/', views.DeleteProf,name='deletepr'),
    path('profit/<pk>/update/', views.UpdatePr,name='updatepr'),


    
    #laporan
    path('laporan/', views.laporan,name='laporan'),

    # page layout paths

    path('page_layout_boxed',views.page_layout_boxed,name='page_layout_boxed'),
    path('page_layout_rtl',views.page_layout_rtl,name='page_layout_rtl'),
    path('page_layout_dark',views.page_layout_dark,name='page_layout_dark'),
    path('page_layout_hide_nav_scroll',views.page_layout_hide_nav_scroll,name='page_layout_hide_nav_scroll'),
    path('page_layout_footer_light',views.page_layout_footer_light,name='page_layout_footer_light'),
    path('page_layout_footer_dark',views.page_layout_footer_dark,name='page_layout_footer_dark'),
    path('page_layout_footer_fixed',views.page_layout_footer_fixed,name='page_layout_footer_fixed'),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)