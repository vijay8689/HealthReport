"""Consistent report exports with escaping and spreadsheet formula protection."""
import csv
import io
import json
from xml.sax.saxutils import escape


def json_report(report):
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def csv_observations(observations):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["Test", "Value", "Comparator", "Unit", "Reference low", "Reference high", "Date", "Review status", "Document ID", "Locator"])
    for o in observations:
        row = [o.name, o.value, o.comparator, o.unit, o.low, o.high, o.date, o.status, o.document_id, o.locator]
        writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v for v in row])
    return stream.getvalue().encode("utf-8-sig")


def pdf_report(report, patient_name):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(595, 842), rightMargin=48, leftMargin=48,
                           topMargin=50, bottomMargin=52)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", fontName="Helvetica-Bold", fontSize=26,
                              leading=32, textColor=colors.HexColor("#087F72"), spaceAfter=10))
    styles["BodyText"].leading = 15
    def para(text, style="BodyText"):
        return Paragraph(escape(str(text)), styles[style])
    parts = [para("HealthLens AI", "Brand"), para("Clinical document intelligence", "Heading2"),
             para(f"{patient_name} | {report['patient_id']}"),
             para(f"SYNTHETIC DEMONSTRATION | {report['status'].upper()} | {report['created_at'][:10]}"),
             Spacer(1, 0.2 * inch), para("Source-grounded observations", "Heading2")]
    for claim in report["claims"]:
        parts.extend([para(claim["text"]), para(f"Source: {claim['document_id']} / {claim['locator']}", "Italic"), Spacer(1, 10)])
    for title, items in [("Data gaps", report["gaps"]), ("Limitations", report["limitations"])]:
        parts.append(para(title, "Heading2"))
        for item in items or ["None identified in the supported fields."]:
            parts.extend([para(item), Spacer(1, 5)])
    def footer(canvas, pdf):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#637786"))
        canvas.drawString(48, 28, "HealthLens AI | Research and education only | Synthetic data")
        canvas.drawRightString(547, 28, str(pdf.page))
    doc.build(parts, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()

