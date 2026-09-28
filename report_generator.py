from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf(res, fixture):
    path = "HydroVision_Audit_Report.pdf"
    c = canvas.Canvas(path, pagesize=letter)
    
    # Title Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "HydroVision AI - Diagnostic Audit Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "Computer Vision & Bernoulli Fluid Dynamics Analysis")
    c.line(50, 725, 550, 725)
    
    # Fixture Details section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 690, "Fixture & Diagnostics Overview")
    c.setFont("Helvetica", 11)
    c.drawString(70, 670, f"Selected Fixture: {fixture}")
    c.drawString(70, 650, f"Diagnostic Status: {res['status']}")
    c.drawString(70, 630, f"Volumetric Flow Rate: {res['flow_lpm']} LPM")
    c.drawString(70, 610, f"Line Pressure: {res['pressure_bar']} Bar")
    c.drawString(70, 590, f"Reynolds Number: {res['reynolds']} ({res['regime']})")
    c.drawString(70, 570, f"Orifice Constriction / Clog: {res['clog_pct']}%")
    
    # Financial and Environmental Impact section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 530, "Environmental & Financial Impact")
    c.setFont("Helvetica", 11)
    c.drawString(70, 510, f"Monthly Excess Water Waste: {res['monthly_waste_l']} Liters")
    c.drawString(70, 490, f"Estimated Financial Penalty: ₹ {res['cost_inr']}")
    c.drawString(70, 470, f"Carbon Footprint: {res['co2_kg']} kg CO2e")
    
    # Recommendations section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 430, "Prescriptive Recommendation")
    c.setFont("Helvetica", 10)
    c.drawString(70, 410, res['action'])
    
    c.save()
    return path