from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime


def export_client_dashboard_pdf(fund_data, client_name=None, output_path="client_dashboard.pdf"):
    """
    Creates a branded FidSync client dashboard PDF with selected fund data and rationale.

    Parameters:
        fund_data (list of dict): Each dict should have:
            - 'fund_name': str
            - 'key_metrics': str or list of str
            - 'rationale': str
        client_name (str): Optional name to include on the cover
        output_path (str): File path to save the PDF
    """
    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER
    margin = 1 * inch

    def write_title(text, y):
        c.setFont("Times-Bold", 20)
        c.setFillColorRGB(0.1, 0.2, 0.5)
        c.drawCentredString(width / 2, y, text)

    def write_subtext(text, y, font="Times-Roman", size=12):
        c.setFont(font, size)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawCentredString(width / 2, y, text)

    # === Cover Page ===
    y = height - inch
    write_title("FidSync Beta – Client Dashboard", y)
    y -= 0.75 * inch

    if client_name:
        write_subtext(f"For: {client_name}", y, font="Times-Italic", size=14)
        y -= 0.5 * inch

    write_subtext(f"Prepared on {datetime.now().strftime('%B %d, %Y')}", y)

    c.showPage()

    # === Fund Pages ===
    for fund in fund_data:
        y = height - margin
        c.setFont("Times-Bold", 16)
        c.setFillColorRGB(0.1, 0.2, 0.5)
        c.drawString(margin, y, fund.get("fund_name", "Unnamed Fund"))
        y -= 0.4 * inch

        # Key Metrics
        c.setFont("Times-Roman", 12)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(margin, y, "Key Metrics:")
        y -= 0.25 * inch

        key_metrics = fund.get("key_metrics", "")
        if isinstance(key_metrics, list):
            metrics = key_metrics
        else:
            metrics = key_metrics.split("\n")

        for line in metrics:
            c.drawString(margin + 0.3 * inch, y, f"• {line.strip()}")
            y -= 0.2 * inch

        y -= 0.3 * inch
        c.drawString(margin, y, "Rationale:")
        y -= 0.25 * inch

        rationale = fund.get("rationale", "")
        rationale_lines = split_text(rationale, 90)
        for line in rationale_lines:
            c.drawString(margin + 0.3 * inch, y, line)
            y -= 0.2 * inch
            if y < 1.2 * inch:
                c.showPage()
                y = height - margin

        c.showPage()

    # === Closing Page ===
    c.setFont("Times-Bold", 18)
    c.setFillColorRGB(0.1, 0.2, 0.5)
    c.drawCentredString(width / 2, height / 2, "Thank you for using FidSync Beta")

    c.save()


def split_text(text, max_chars):
    """
    Splits long text into lines of max character length.
    """
    words = text.split()
    lines = []
    line = ""
    for word in words:
        if len(line + word) < max_chars:
            line += word + " "
        else:
            lines.append(line.strip())
            line = word + " "
    if line:
        lines.append(line.strip())
    return lines
