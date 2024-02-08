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