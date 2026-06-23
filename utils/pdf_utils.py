import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_escalation_pdf(qr_id: str, shop_name: str, reports: list,
                             escalation_count: int, shop_address: str = "") -> str:
    """
    Generate a professional PDF escalation report.
    Returns file path of generated PDF.
    """
    if not REPORTLAB_AVAILABLE:
        return None

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "reports")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"escalation_{qr_id}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Title ────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#c0392b'),
        spaceAfter=6, alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'SubTitle', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=4, alignment=TA_CENTER
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#2c3e50'),
        spaceBefore=12, spaceAfter=4,
        borderPad=4
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#2c3e50'),
        spaceAfter=3
    )

    elements.append(Paragraph("🔴 COUNTERFEIT ESCALATION REPORT", title_style))
    elements.append(Paragraph("VeriScan Anti-Counterfeiting Platform", subtitle_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p IST')}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#c0392b')))
    elements.append(Spacer(1, 0.4*cm))

    # ── Priority Badge ────────────────────────────────────────
    priority = "CRITICAL" if escalation_count >= 10 else "HIGH"
    priority_color = colors.HexColor('#c0392b') if priority == "CRITICAL" else colors.HexColor('#e67e22')
    priority_data = [[f"PRIORITY: {priority}  |  {escalation_count} Independent Reports"]]
    priority_table = Table(priority_data, colWidths=[16*cm])
    priority_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), priority_color),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [priority_color]),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(priority_table)
    elements.append(Spacer(1, 0.5*cm))

    # ── Incident Summary ─────────────────────────────────────
    elements.append(Paragraph("INCIDENT SUMMARY", section_style))
    summary_data = [
        ["Field", "Details"],
        ["QR Code ID", qr_id],
        ["Shop / Location", shop_name],
        ["Address", shop_address or "Not provided"],
        ["Total Reports", str(escalation_count)],
        ["Escalation Date", datetime.now().strftime("%d %b %Y")],
        ["Status", "REQUIRES IMMEDIATE ACTION"],
    ]
    summary_table = Table(summary_data, colWidths=[5*cm, 11*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4*cm))

    # ── Reports Table ─────────────────────────────────────────
    elements.append(Paragraph("INDIVIDUAL REPORTS", section_style))
    report_data = [["#", "Reporter", "Anomaly", "Date", "GPS"]]
    for i, r in enumerate(reports[:20], 1):
        lat = r.get('latitude', '')
        lon = r.get('longitude', '')
        gps = f"{lat:.4f}, {lon:.4f}" if lat and lon else "N/A"
        report_data.append([
            str(i),
            r.get('reporter_name', 'Anonymous')[:20],
            r.get('anomaly_type', 'N/A')[:25],
            r.get('reported_at', '')[:10],
            gps
        ])
    report_table = Table(report_data, colWidths=[0.8*cm, 3.5*cm, 5*cm, 2.5*cm, 4.2*cm])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(report_table)
    elements.append(Spacer(1, 0.5*cm))

    # ── Legal / Action Section ────────────────────────────────
    elements.append(Paragraph("RECOMMENDED ACTIONS", section_style))
    actions = [
        "1. Dispatch field investigation team to the reported location immediately.",
        "2. Coordinate with local law enforcement and IP crime cell.",
        "3. File complaint with National Consumer Helpline (1915).",
        "4. Initiate legal proceedings under Trademarks Act, 1999 (Section 103).",
        "5. Consider filing with NITI Aayog Anti-Counterfeiting Portal.",
        "6. Issue product recall advisory if necessary.",
    ]
    for action in actions:
        elements.append(Paragraph(action, body_style))

    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7')))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "This report was auto-generated by VeriScan Crowd Aggregation Engine. "
        "Evidence is crowd-sourced from independent consumer reports.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#95a5a6'), alignment=TA_CENTER)
    ))

    doc.build(elements)
    return filepath
