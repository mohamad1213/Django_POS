from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

    # dashboard paths

    path('', views.LandingPage,name='landingpage'),
    path('tentang/', views.Tentang,name='tentang'),
    path('layanan/', views.Layanan,name='layanan'),
    path('produk/', views.Produk,name='produk'),
    path('galeri/', views.Galeri,name='galeri'),
    path('kontak/', views.Kontak,name='kontak'),
    path('dashboard/', views.indexPage,name='dashboard'),
    path('api/product-summary/', views.get_product_summary, name='product_summary'),
    path('products/analysis/',views.product_analysis,name='product_analysis'),


    # POS
    path('product/', include('products.urls')),
    path('pegawai/', include('pegawai.urls')),
    path('customer/', include('customers.urls')),
    path('accounts/', include('authentication.urls')),
    
    # Transaksi 
    path('sales/', include('sales.urls')), # POS Penjualan (Barang Keluar)
    path('purchases/', include('purchases.urls')), # POS Pembelian (Barang Masuk)
    path('afkiran/', include('afkiran.urls', namespace='afkiran')), # Afkiran Sortir PS Kaca
    # Input Manual
    path('transaksi/', views.transaksi,name='transaksi'), 
    path('transaksi/<int:pk>/update/', views.UpdateTr,name='updatetr'),
    path('transaksi/<pk>/delete/', views.DeleteTr,name='deletetr'),
    path('transaksi/delete-multiple/',views.delete_multiple_transaksi,name='transaksi_delete_multiple'),
    #Riwayat Transaski
    path('transaksi-history/', views.transaksi_history,name='transaksi_history'),
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
    path('profit/create/', views.profit_create,name='profit_create'),
    path('profit/<pk>/delete/', views.DeleteProf,name='deletepr'),
    path('profit/<pk>/update/', views.UpdatePr,name='updatepr'),
    path('profit/<pk>/view/', views.ViewProf,name='viewprof'),
    path('profit/<pk>/tabung/', views.profit_mark_tabung,name='profit_mark_tabung'),
    # path('profit_today_json/', views.profit_today_json, name='profit_today_json'),

    # Biaya Bulanan
    path('biaya-bulanan/', views.biaya_bulanan_list, name='biaya_bulanan_list'),
    path('biaya-bulanan/create/', views.biaya_bulanan_create, name='biaya_bulanan_create'),
    path('biaya-bulanan/<int:pk>/update/', views.biaya_bulanan_update, name='biaya_bulanan_update'),
    path('biaya-bulanan/<int:pk>/delete/', views.biaya_bulanan_delete, name='biaya_bulanan_delete'),

    
    
    path('stok/', views.stockin_list,name='stockin_list'),
    path('stok/create/', views.stockin_create,name='stockin_create'),
    path("stockin/update/<int:pk>/", views.stockin_update, name="stockin_update"),
    path("stockin/delete/<int:pk>/", views.stockin_delete, name="stockin_delete"),
    path("api/products/", views.product_search_api, name="product_search_api"),
    
    
    # ChimiAI Assistant
    path('chimiai/', views.chimi_ai_page, name='chimi_ai_page'),
    path('api/chimiai/chat/', views.chimi_ai_chat, name='chimi_ai_chat'),
    path('api/chimiai/summary/', views.get_chimi_ai_summary, name='chimi_ai_summary'),

    #laporan
    path('laporan/', views.laporan, name='laporan'),
    path('chart-report/', views.ChartReport , name='chart-report'),
    # path('export-to-excel/',views.export_to_excel, name='export_to_excel'),
    # path('export-to-pdf/', views.export_to_pdf, name='export_to_pdf'),

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