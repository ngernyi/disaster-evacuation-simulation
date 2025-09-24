from flask import Flask, send_file, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import tempfile
import os
import csv
from datetime import datetime

def export_csv():
    # Example data - replace with your actual DB data
    data = [
        {'id': 1, 'name': 'Simulation 1', 'date': '2025-06-19', 'duration': 120},
        {'id': 2, 'name': 'Simulation 2', 'date': '2025-06-18', 'duration': 95}
    ]

    # Create CSV in text mode first
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'name', 'date', 'duration'])
    writer.writeheader()
    writer.writerows(data)

    # Convert StringIO to BytesIO for sending
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))  # encode to bytes
    mem.seek(0)
    return mem

def export_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setTitle("Flask PDF Report")
    c.drawString(100, 750, "Simulation Report")
    c.drawString(100, 730, "Generated successfully via Flask + ReportLab!")
    c.showPage()
    c.save()

    buffer.seek(0)  # Important: rewind the buffer to the start!
    return buffer
    


# Alternative method using temporary file (use this if above doesn't work)
def export_pdf_alternative():
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    # Create a PDF document
    p.drawString(100, 750, "Book Catalog")

    y = 700
    for book in user_data:
        p.drawString(100, y, f"Title: {book['title']}")
        p.drawString(100, y - 20, f"Author: {book['author']}")
        p.drawString(100, y - 40, f"Year: {book['publication_year']}")
        y -= 60

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    app.run(debug=True)