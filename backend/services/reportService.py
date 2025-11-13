from flask import Flask, send_file, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io
import tempfile
import os
import csv
from datetime import datetime
from services.simulationService import *

def export_csv(simulation_id):
    # Fetch data
    simulation_data = get_simulation_metadata(simulation_id)
    evacuees = get_simulation_evacuees(simulation_id)
    hazards = get_simulation_hazards(simulation_id)

    # Compute evacuee routes and max duration
    evacuees_routes = []
    duration = 0
    for evacuee in evacuees:
        route = get_evacuees_route(evacuee.get('Evacuee_Id'))
        route_len = len(route['route']) if route else 0
        evacuees_routes.append(route_len)
        duration = max(duration, route_len)

    # Prepare CSV row
    data = [
        {
            'Simulation Name': simulation_data.get('Simulation_Name'),
            'Created At': simulation_data.get('Created_At'),
            'Status': simulation_data.get('Status'),
            'Computational Time': simulation_data.get('Computational_Time'),
            'Evacuees': len(evacuees),
            'Hazards': len(hazards),
            'Duration': duration
        }
    ]

    # Create CSV in memory
    output = io.StringIO()
    fieldnames = ['Simulation Name', 'Created At', 'Status', 'Computational Time', 'Evacuees', 'Hazards', 'Duration']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

    # Convert to BytesIO for Flask send_file
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return mem

def export_pdf(simulation_id):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Fetch simulation data from DB
    simulation_data = get_simulation_metadata(simulation_id)
    evacuees = get_simulation_evacuees(simulation_id)
    hazards = get_simulation_hazards(simulation_id)
    evacuees_routes = []
    duration = 0
    for evacuee in evacuees:
        route = get_evacuees_route(evacuee.get('Evacuee_Id'))
        evacuees_routes.append(len(route) if route else 0)
        duration = max(duration, len(route) if route else 0)


    c.setTitle("Simulation Report - " + str(simulation_data.get('Simulation_Name')))
    c.setFont("Helvetica", 12)
    # Add simulation details
    c.drawString(100, 750, "Simulation Details:")
    c.drawString(100, 730, f"Simulation Name: {simulation_data.get('Simulation_Name')}")
    c.drawString(100, 710, f"Created At: {simulation_data.get('Created_At')}")
    c.drawString(100, 690, f"Status: {simulation_data.get('Status')}")
    c.drawString(100, 670, f"Computational Time: {simulation_data.get('Computational_Time')} ms")
    c.drawString(100, 650, f"Evacuees: {len(evacuees)}")
    c.drawString(100, 630, f"Hazards: {len(hazards)}")
    c.drawString(100, 610, f"Evacuees Routes: {evacuees_routes}")
    
    # c.drawString(100, 750, "Simulation Report")
    # c.drawString(100, 730, "Generated successfully via Flask + ReportLab!")
    c.showPage()
    c.save()

    buffer.seek(0)  # Important: rewind the buffer to the start!
    return buffer
    
def export_pdf(simulation_id):
    # Create in-memory buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()
    story = []

    # 🏷️ Title
    title_style = styles['Title']
    story.append(Paragraph("Simulation Report", title_style))
    story.append(Spacer(1, 12))

    # Fetch data
    simulation_data = get_simulation_metadata(simulation_id)
    evacuees = get_simulation_evacuees(simulation_id)
    hazards = get_simulation_hazards(simulation_id)
    evacuees_routes = []
    duration = 0
    for evacuee in evacuees:
        route = get_evacuees_route(evacuee.get('Evacuee_Id'))
        evacuees_routes.append(len(route['route']) if route else 0)
        duration = max(duration, len(route['route']) if route else 0)

    # 🧾 Summary Table
    summary_data = [
        ['Simulation Name:', simulation_data.get('Simulation_Name')],
        ['Created At:', simulation_data.get('Created_At')],
        ['Duration:', duration],
        ['Computational Time (ms):', simulation_data.get('Computational_Time')],
        ['Evacuees:', len(evacuees)],
        ['Hazards:', len(hazards)],
    ]

    table = Table(summary_data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EBF5FB')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    # 🧮 Add a graph (see below)
    chart_buffer = generate_evacuee_chart(evacuees_routes)
    story.append(Image(chart_buffer, width=5*inch, height=3*inch))
    story.append(Spacer(1, 12))

    # 📄 Build the document
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_evacuee_chart(evacuees_routes):
    """
    evacuees_routes: list of lists
        Example: [[(x1,y1,z1), (x2,y2,z2)], [(x1,y1)], [(x1,y1),(x2,y2),(x3,y3)]]
    """
    
    # Find the maximum route length (longest path)
    max_length = max(evacuees_routes) if evacuees_routes else 0

    # Simulate escape progress over time
    time_steps = list(range(max_length + 1))
    evacuees_escaped = []

    for t in time_steps:
        count = sum(1 for length in evacuees_routes if length <= t)
        evacuees_escaped.append(count)

    # --- Plot as line chart ---
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(time_steps, evacuees_escaped, marker='o', color="#3498db", linewidth=2)

    ax.set_title("Evacuation Progress Over Time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Number of Evacuees Escaped")
    ax.grid(True, linestyle='--', alpha=0.6)

    # Save chart to memory buffer
    chart_buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(chart_buffer, format='PNG')
    plt.close(fig)
    chart_buffer.seek(0)
    return chart_buffer



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