from flask import Flask, send_file, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import tempfile
import os
import csv
from datetime import datetime
from services.simulationService import *

import io
import csv

def export_csv(simulation_id):
    # 1. Initial Fetch
    simulation_data = get_simulation_metadata(simulation_id)
    if not simulation_data:
        return None

    evaluation_id = simulation_data.get('Evaluation_Id')
    fieldnames = ['Simulation Name', 'Created At', 'Status', 'Computational Time',
                  'Evacuees', 'Hazards', 'Duration', 'High Risk']
    data_rows = []

    # 2. Determine which simulations to process
    if evaluation_id:
        # It's a batch
        simulations_to_process = get_simulations_by_evaluation(evaluation_id)
    else:
        # It's just one
        simulations_to_process = [simulation_data]

    # 3. Get all IDs and fetch stats in ONE batch trip
    sim_ids = [s['Simulation_Id'] for s in simulations_to_process]
    # The underscore _ means "ignore the second return value"
    stats_map, _ = get_export_stats_batch(sim_ids)

    # 4. Identify High Risk (Highest Duration)
    highest_risk_id = None
    if stats_map:
        highest_risk_id = max(stats_map, key=lambda k: stats_map[k]['duration'])

    # 5. Build the data rows using the stats_map (No more DB calls in this loop!)
    for sim in simulations_to_process:
        sid = sim['Simulation_Id']
        stats = stats_map.get(sid, {'evacuees': 0, 'hazards': 0, 'duration': 0})
        
        data_rows.append({
            'Simulation Name': sim['Simulation_Name'],
            'Created At': sim['Created_At'],
            'Status': sim['Status'],
            'Computational Time': round(float(sim.get('Computational_Time') or 0), 5),
            'Evacuees': stats['evacuees'],
            'Hazards': stats['hazards'],
            'Duration': stats['duration'],
            'High Risk': 'Yes' if (evaluation_id and sid == highest_risk_id) else ''
        })

    # 6. Create CSV in memory (Best for Render)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data_rows)

    # Convert to bytes for Flask response
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return mem
# def export_csv(simulation_id):
#     # Fetch data
#     simulation_data = get_simulation_metadata(simulation_id)
#     evaluation_id = simulation_data.get('Evaluation_Id')

#     # Prepare CSV fieldnames
#     fieldnames = ['Simulation Name', 'Created At', 'Status', 'Computational Time',
#                   'Evacuees', 'Hazards', 'Duration', 'High Risk']

#     data = []

#     if evaluation_id:
#         # Batch simulations
#         batch_simulations = get_simulations_by_evaluation(evaluation_id)

#         # Compute duration for each
#         for sim in batch_simulations:
#             evacuees_routes = [
#                 len(get_evacuees_route(e.get('Evacuee_Id'))['route']) if get_evacuees_route(e.get('Evacuee_Id')) else 0
#                 for e in get_simulation_evacuees(sim['Simulation_Id'])
#             ]
#             sim['Duration_sec'] = max(evacuees_routes, default=0) / 50

#         # Find highest-risk simulation
#         highest_risk_sim = max(batch_simulations, key=lambda x: x['Duration_sec'], default=None)

#         # Add batch rows
#         for sim in batch_simulations:
#             data.append({
#                 'Simulation Name': sim['Simulation_Name'],
#                 'Created At': sim['Created_At'],
#                 'Status': sim['Status'],
#                 'Computational Time': round(sim['Computational_Time'], 5),
#                 'Evacuees': len(get_simulation_evacuees(sim['Simulation_Id'])),
#                 'Hazards': len(get_simulation_hazards(sim['Simulation_Id'])),
#                 'Duration': sim['Duration_sec'],
#                 'High Risk': 'Yes' if sim['Simulation_Id'] == highest_risk_sim['Simulation_Id'] else ''
#             })
#     else:
#         # Single simulation
#         evacuees = get_simulation_evacuees(simulation_id)
#         hazards = get_simulation_hazards(simulation_id)
#         evacuees_routes = [
#             len(get_evacuees_route(e.get('Evacuee_Id'))['route']) if get_evacuees_route(e.get('Evacuee_Id')) else 0
#             for e in evacuees
#         ]
#         duration = max(evacuees_routes, default=0) / 50
#         data.append({
#             'Simulation Name': simulation_data.get('Simulation_Name'),
#             'Created At': simulation_data.get('Created_At'),
#             'Status': simulation_data.get('Status'),
#             'Computational Time': round(simulation_data.get('Computational_Time',0), 5),
#             'Evacuees': len(evacuees),
#             'Hazards': len(hazards),
#             'Duration': duration,
#             'High Risk': ''
#         })

#     # Create CSV in memory
#     output = io.StringIO()
#     writer = csv.DictWriter(output, fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(data)

#     # Convert to BytesIO for Flask send_file
#     mem = io.BytesIO()
#     mem.write(output.getvalue().encode('utf-8'))
#     mem.seek(0)
#     return mem


# def export_pdf(simulation_id):
#     buffer = io.BytesIO()
#     c = canvas.Canvas(buffer, pagesize=A4)
    
#     # Fetch simulation data from DB
#     simulation_data = get_simulation_metadata(simulation_id)
#     evacuees = get_simulation_evacuees(simulation_id)
#     hazards = get_simulation_hazards(simulation_id)
#     evacuees_routes = []
#     duration = 0
#     for evacuee in evacuees:
#         route = get_evacuees_route(evacuee.get('Evacuee_Id'))
#         evacuees_routes.append(len(route) if route else 0)
#         duration = max(duration, len(route) if route else 0)


#     c.setTitle("Simulation Report - " + str(simulation_data.get('Simulation_Name')))
#     c.setFont("Helvetica", 12)
#     # Add simulation details
#     c.drawString(100, 750, "Simulation Details:")
#     c.drawString(100, 730, f"Simulation Name: {simulation_data.get('Simulation_Name')}")
#     c.drawString(100, 710, f"Created At: {simulation_data.get('Created_At')}")
#     c.drawString(100, 690, f"Status: {simulation_data.get('Status')}")
#     c.drawString(100, 670, f"Computational Time: {simulation_data.get('Computational_Time')} ms")
#     c.drawString(100, 650, f"Evacuees: {len(evacuees)}")
#     c.drawString(100, 630, f"Hazards: {len(hazards)}")
#     c.drawString(100, 610, f"Evacuees Routes: {evacuees_routes}")
    
#     # c.drawString(100, 750, "Simulation Report")
#     # c.drawString(100, 730, "Generated successfully via Flask + ReportLab!")
#     c.showPage()
#     c.save()

#     buffer.seek(0)  # Important: rewind the buffer to the start!
#     return buffer
    
# def export_pdf(simulation_id):
#     # Create in-memory buffer
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4,
#                             rightMargin=40, leftMargin=40,
#                             topMargin=60, bottomMargin=40)

#     styles = getSampleStyleSheet()
#     story = []

#     # 🏷️ Title
#     title_style = styles['Title']
#     story.append(Paragraph("Simulation Report", title_style))
#     story.append(Spacer(1, 12))

#     # Fetch data
#     simulation_data = get_simulation_metadata(simulation_id)
#     evacuees = get_simulation_evacuees(simulation_id)
#     hazards = get_simulation_hazards(simulation_id)
#     evacuees_routes = []
#     duration = 0
#     for evacuee in evacuees:
#         route = get_evacuees_route(evacuee.get('Evacuee_Id'))
#         evacuees_routes.append(len(route['route']) if route else 0)
#         duration = max(duration, len(route['route']) if route else 0)

#     # 🧾 Summary Table
#     summary_data = [
#         ['Simulation Name:', simulation_data.get('Simulation_Name')],
#         ['Created At:', simulation_data.get('Created_At')],
#         ['Duration(s):', duration/50],
#         ['Computational Time (s):', simulation_data.get('Computational_Time')],
#         ['Evacuees:', len(evacuees)],
#         ['Hazards:', len(hazards)],
#     ]

#     table = Table(summary_data, colWidths=[200, 300])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EBF5FB')),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
#     ]))

#     story.append(table)
#     story.append(Spacer(1, 20))

#     # 🧮 Add a graph (see below)
#     chart_buffer = generate_evacuee_chart(evacuees_routes)
#     story.append(Image(chart_buffer, width=5*inch, height=3*inch))
#     story.append(Spacer(1, 12))
    
#     evaluation_id = simulation_data.get('Evaluation_Id')
#     if evaluation_id is not None:
#          # 🏷️ Page 2 Title
#         story.append(Paragraph(
#             "High-Risk Session Analysis",
#             styles['Title']
#         ))
#         story.append(Spacer(1, 12))

#         # Fetch batch simulations
#         batch_simulations = get_simulations_by_evaluation(evaluation_id)

#         analysis_data = [['Simulation Name', 'Evacuees', 'Duration (s)', 'Computational Time (s)']]

#         for sim in batch_simulations:
#             evacuees = get_simulation_evacuees(sim['Simulation_Id'])
#             evacuee_count = len(evacuees)

#             max_steps = 0
#             for evacuee in evacuees:
#                 route = get_evacuees_route(evacuee.get('Evacuee_Id'))
#                 if route:
#                     max_steps = max(max_steps, len(route['route']))

#             # Convert steps → seconds
#             duration_seconds = max_steps / 50

#             # Format computational time
#             comp_time = round(sim['Computational_Time'], 5)

#             sim['Duration'] = duration_seconds

#             analysis_data.append([
#                 sim['Simulation_Name'],
#                 evacuee_count,
#                 f"{duration_seconds:.2f}",   # duration shown nicely
#                 f"{comp_time:.5f}"
#             ])


#         analysis_table = Table(analysis_data, colWidths=[200, 120, 120])
#         analysis_table.setStyle(TableStyle([
#             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#             ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D6EAF8')),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
#         ]))

#         story.append(analysis_table)
#         story.append(Spacer(1, 20))

#         # 📊 Comparison Graph
#         comparison_chart = generate_batch_comparison_chart(batch_simulations)
#         story.append(Image(comparison_chart, width=5*inch, height=3*inch))
        
#         # HIGH RISK SESSION
#         # Identify highest-risk simulation (longest duration)
#         highest_risk_sim = max(
#             batch_simulations,
#             key=lambda sim: sim.get('Duration', 0),
#             default=None
#         )

#         story.append(Spacer(1, 16))
#         story.append(Paragraph(
#             "High-Risk Session Summary",
#             styles['Heading2']
#         ))
#         story.append(Spacer(1, 8))
        
#         if highest_risk_sim:
#             risk_text = f"""
#             Among all simulations in this batch, 
#             <b>{highest_risk_sim['Simulation_Name']}</b> was identified as the 
#             <b>highest-risk session</b>. This simulation recorded the longest 
#             evacuation duration of <b>{highest_risk_sim['Duration']:.2f} seconds</b>, 
#             indicating slower evacuation performance and increased exposure to hazards.
#             """

#             story.append(Paragraph(risk_text, styles['BodyText']))


        

#     # 📄 Build the document
#     doc.build(story)
#     buffer.seek(0)
#     return buffer

def export_pdf(simulation_id):
    simulation_data = get_simulation_metadata(simulation_id)
    if not simulation_data:
        return None
    
    evaluation_id = simulation_data.get('Evaluation_Id')
    
    if evaluation_id:
        batch_simulations = get_simulations_by_evaluation(evaluation_id)
        sim_ids = [s['Simulation_Id'] for s in batch_simulations]
    else:
        batch_simulations = [simulation_data]
        sim_ids = [simulation_id]

    # Get Batch Stats AND the individual route list for the chart
    stats_map, evac_routes_list = get_export_stats_batch(sim_ids, target_sim_id=simulation_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Simulation Report", styles['Title']))
    story.append(Spacer(1, 12))

    current_stats = stats_map.get(simulation_id, {'evacuees': 0, 'hazards': 0, 'duration': 0})
    
    # Summary Table
    summary_data = [
        ['Simulation Name:', simulation_data.get('Simulation_Name')],
        ['Created At:', simulation_data.get('Created_At')],
        ['Duration(s):', f"{current_stats['duration']:.2f}"],
        ['Computational Time (s):', f"{float(simulation_data.get('Computational_Time') or 0):.5f}"],
        ['Evacuees:', current_stats['evacuees']],
        ['Hazards:', current_stats['hazards']],
    ]

    table = Table(summary_data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # 📊 Page 1 Graph (Progress over time)
    if evac_routes_list:
        chart_buffer = generate_evacuee_chart(evac_routes_list) 
        story.append(Image(chart_buffer, width=5*inch, height=3*inch))
    
    # Batch Analysis
    if evaluation_id:
        story.append(PageBreak())
        story.append(Paragraph("High-Risk Session Analysis", styles['Title']))
        story.append(Spacer(1, 12))

        analysis_data = [['Simulation Name', 'Evacuees', 'Duration (s)', 'Comp. Time (s)']]
        for sim in batch_simulations:
            sid = sim['Simulation_Id']
            s_stats = stats_map.get(sid, {'evacuees': 0, 'duration': 0})
            sim['Duration'] = s_stats['duration'] # Used for comparison chart

            analysis_data.append([
                sim['Simulation_Name'],
                s_stats['evacuees'],
                f"{s_stats['duration']:.2f}",
                f"{float(sim.get('Computational_Time') or 0):.5f}"
            ])

        analysis_table = Table(analysis_data, colWidths=[180, 80, 80, 100])
        analysis_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D6EAF8')),
        ]))
        story.append(analysis_table)

        # 📊 Comparison Graph
        comparison_chart = generate_batch_comparison_chart(batch_simulations)
        story.append(Image(comparison_chart, width=5*inch, height=3*inch))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_evacuee_chart(evacuees_routes, steps_per_second=50):
    if not evacuees_routes:
        return None

    # 1. Sort the routes (This is much faster than creating a list of 30,000 zeros)
    sorted_steps = sorted(evacuees_routes)
    total_evacuees = len(sorted_steps)
    
    # 2. Build time and count arrays
    # We start at time 0 with 0 people escaped
    time_seconds = [0]
    escaped_sampled = [0]
    
    count = 0
    for step in sorted_steps:
        count += 1
        time_seconds.append(step / steps_per_second)
        escaped_sampled.append(count)

    # 3. Plotting (Optimized for speed)
    # Use 'drawstyle' to make it a step-chart, which looks more professional for evacuation
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.step(time_seconds, escaped_sampled, where='post', linewidth=2, color='#2E86C1')

    ax.set_title("Evacuation Progress Over Time")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Number of Evacuees Escaped")
    ax.set_ylim(0, total_evacuees + 1) # Ensure Y axis looks clean
    ax.grid(True, linestyle='--', alpha=0.6)

    # Save to buffer
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format="PNG", dpi=100) # Lower DPI saves processing time
    plt.close(fig)
    buffer.seek(0)

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

def generate_batch_comparison_chart(batch_simulations):
    """
    Generates a bar chart comparing evacuation durations for multiple simulations.

    :param batch_simulations: list of dicts, each with keys:
        - 'Simulation_Name'
        - 'Duration' (int)
    :return: io.BytesIO buffer containing the PNG chart
    """
    # Extract names and durations
    sim_names = [sim['Simulation_Name'] for sim in batch_simulations]
    durations = [sim['Duration'] for sim in batch_simulations]

    # Create figure
    plt.figure(figsize=(8, 4))
    bars = plt.bar(sim_names, durations, color='#2E86C1')

    # Add data labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{height}',
            ha='center',
            va='bottom',
            fontsize=8
        )

    # Labels and title
    plt.xlabel("Simulation")
    plt.ylabel("Evacuation Duration (steps)")
    plt.title("High-Risk Session Analysis - Batch Comparison")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save figure to in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()  # Close figure to free memory
    buffer.seek(0)

    return buffer

if __name__ == '__main__':
    app.run(debug=True)
