from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_pdf(summary_text, proposal_html, file_obj):
    """
    Creates a basic PDF summary and saves it to the file_obj (a BytesIO buffer).
    """
    c = canvas.Canvas(file_obj, pagesize=letter)
    width, height = letter
    y = height - 50

    # Add summary title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Summary")
    y -= 30

    # Add summary content
    c.setFont("Helvetica", 10)
    for line in summary_text.split('\n'):
        c.drawString(50, y, line)
        y -= 15

    # Proposal section
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Proposal")
    y -= 30

    c.setFont("Helvetica", 10)
    for line in proposal_html.split('\n'):
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line)
        y -= 15

    c.showPage()
    c.save()
