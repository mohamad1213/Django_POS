`````def generate_chart_data(data, interval):
    chart_data = []

    if interval == 'daily':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'],
                'jumlah': entry['jumlah'],
            })
    elif interval == 'monthly':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'].strftime('%B %Y'),  # Format as Month Year
                'jumlah': entry['jumlah'],
            })
    elif interval == 'yearly':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'].year,
                'jumlah': entry['jumlah'],
            })

    return chart_data
def generate_pdf(request):
    data = Transaksi.objects.all().order_by('-tanggal','-id')
    context_data = {
        'data': data,
    }
            

    # Render the HTML template with the invoice data
    template = get_template('generatepdf.html')
    html = template.render(context_data)

    # Create a BytesIO buffer to write the PDF content
    pdf_buffer = BytesIO()

    # Use xhtml2pdf to generate the PDF from the HTML content
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)

    if pisa_status.err:
        return HttpResponse('Error creating PDF', content_type='text/plain')

    # Set the buffer's file pointer to the beginning
    pdf_buffer.seek(0)

    # Create a response with the PDF content
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'filename=invoice.pdf'

    return response
def generate_chart_data(data, interval):
    chart_data = []

    if interval == 'daily':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'],
                'jumlah': entry['jumlah'],
            })
    elif interval == 'monthly':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'].strftime('%B %Y'),  # Format as Month Year
                'jumlah': entry['jumlah'],
            })
    elif interval == 'yearly':
        for entry in data:
            chart_data.append({
                'tanggal': entry['tanggal'].year,
                'jumlah': entry['jumlah'],
            })

    return chart_data

# def chart_data(request):
#   # Hitung tanggal awal sesuai dengan periode waktu yang diminta
#     start_date = datetime.now() - timedelta(days=365)
#     categories = Kategori.objects.all()
#     data = []

#     for kategori in categories:
#         total_amount = Transaksi.objects.filter(kategori=kategori).aggregate(Sum('jumlah'))['jumlah__sum'] or 0
#         data.append({'kategori': kategori.nama, 'jumlah': float(total_amount)})

#     labels_don = [item['kategori'] for item in data]
#     values_don = [float(item['jumlah']) for item in data]
#     # Ambil data sesuai dengan periode waktu yang diminta
#     data_pemasukan = Transaksi.objects \
#         .filter(tanggal__gte=start_date, transaksi_choice='P') \
#         .extra({'month': "EXTRACT(month FROM tanggal)"}) \
#         .values('month') \
#         .annotate(jumlah=models.Sum('jumlah')) \
#         .order_by('month')
#     data_pengeluaran = Transaksi.objects \
#         .filter(tanggal__gte=start_date, transaksi_choice='L') \
#         .extra({'month': "EXTRACT(month FROM tanggal)"}) \
#         .values('month') \
#         .annotate(jumlah=models.Sum('jumlah')) \
#         .order_by('month')
#     data_labels= Transaksi.objects \
#         .filter(tanggal__gte=start_date) \
#         .extra({'month': "EXTRACT(month FROM tanggal)"}) \
#         .values('month') \
#         .annotate(jumlah=models.Sum('jumlah')) \
#         .order_by('month')
#     data = Transaksi.objects.values('tanggal').annotate(total_nominal=Sum('jumlah'))
    
#     # Daftar nama bulan untuk label
#     month_names = [
#         "Jan",
#         "Feb",
#         "Mar",
#         "Apr",
#         "May",
#         "Jun",
#         "Jul",
#         "Aug",
#         "Sep",
#         "Oct",
#         "Nov",
#         "Dec",
#     ]
#     # Format tanggal sesuai dengan periode waktu yang diminta
#     labels = [month_names[int(entry['month']) - 1] for entry in data_labels]
#     # values = [entry['jumlah'] for entry in data]
#     dates = [entry['tanggal'] for entry in data]
#     print(dates)
#     values_pemasukan = [entry['jumlah'] if 'jumlah' in entry else 0 for entry in data_pemasukan]
#     values_pengeluaran = [entry['jumlah'] if 'jumlah' in entry else 0 for entry in data_pengeluaran]
#     count = Transaksi.objects.count()
#     print(count)
#     return JsonResponse(data={
#         'labels': labels, 
#         'labels_don': labels_don, 
#         'values_don': values_don, 
#         'dates': dates, 
#         'count': count, 
#         'values_pemasukan': values_pemasukan,
#         'values_pengeluaran': values_pengeluaran
        
#         })
    # income_data = Transaksi.objects.filter(transaksi_choice='P').values('tanggal__date').annotate(total_jumlah=Sum('jumlah'))
    # expense_data = Transaksi.objects.filter(transaksi_choice='L').values('tanggal__date').annotate(total_jumlah=Sum('jumlah'))

    # labels = list(set(entry['tanggal__date'] for entry in income_data))
    # labels.extend(set(entry['tanggal__date'] for entry in expense_data))
    # labels = list(set(labels))
    # labels.sort()  # Sort the dates chronologically
    # print(labels)