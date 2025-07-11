# utils/pdf_exporter.py
from fpdf import FPDF
from datetime import datetime

class UniversalFidSyncPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(33, 37, 41)  # Dark gray
        self.set_fill_color(235, 241, 255)  # Light blue banner
        self.cell(0, 12, "FidSync Beta", ln=True, align="C", fill=True)
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 8, f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_content(self, title, body_lines):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, title, ln=True)
        self.set_font("Helvetica", "", 11)
        for line in body_lines:
            self.multi_cell(0, 6, line)
        self.ln(4)


def create_pdf_with_fidsync_banner(content_sections, output_path="fidsync_output.pdf"):
    """
    content_sections: list of dicts like:
        [
            {"title": "Section 1", "body": ["Line 1", "Line 2"]},
            {"title": "Fund A", "body": ["Status: Pass", "Tenure: 5 years"]},
        ]
    """
    pdf = UniversalFidSyncPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    for section in content_sections:
        pdf.add_content(section.get("title", "Untitled"), section.get("body", []))

    pdf.output(output_path)
    return output_path

#To Go Into Py's

#from utils.pdf_exporter import create_pdf_with_fidsync_banner

#content = [
    #{"title": "Summary", "body": ["This document summarizes the extracted data."]},
   # {"title": "Fund A", "body": ["Status: Pass", "Tenure: 5 years", "Expense Ratio: 0.45%"]}
#]

#create_pdf_with_fidsync_banner(content, output_path="fund_results.pdf")
