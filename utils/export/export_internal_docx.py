from docx import Document
from docx.shared import Pt, Inches
from datetime import datetime
import os
from bs4 import BeautifulSoup

def add_clean_html_paragraphs(doc, html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    for elem in soup.contents:
        if elem.name == "h3":
            para = doc.add_paragraph()
            run = para.add_run(elem.get_text())
            run.bold = True
            run.font.size = Pt(14)
        elif elem.name == "b":
            para = doc.add_paragraph()
            run = para.add_run(elem.get_text())
            run.bold = True
        elif elem.name == "em":
            para = doc.add_paragraph()
            run = para.add_run(elem.get_text())
            run.italic = True
        elif elem.name == "ul":
            for li in elem.find_all("li"):
                doc.add_paragraph(li.get_text(), style='List Bullet')
        elif elem.name == "br":
            doc.add_paragraph("")
        elif elem.string and elem.string.strip():
            doc.add_paragraph(elem.string.strip())

def export_internal_docx(df, proposal_text, doc_path, user="Cameron Rodrigues", firm="Procyon Partners", logo_path=None):
    doc = Document()
    font = doc.styles['Normal'].font
    font.name = "Times New Roman"
    font.size = Pt(12)

    section = doc.sections[0]
    header = section.header
    header.paragraphs[0].text = f"Internal Use Only | Prepared by {user} | {firm} | {datetime.now().strftime('%B %d, %Y')}"

    if logo_path and os.path.exists(logo_path):
        doc.add_picture(logo_path, width=Inches(2.5))

    doc.add_paragraph("Internal Proposal Review", style="Title")
    doc.add_paragraph("This document summarizes key performance metrics and relative positioning of selected funds. Not intended for client distribution.\n")

    add_clean_html_paragraphs(doc, proposal_text)

    doc.add_paragraph("Generated by FidSync Beta – For internal strategic review only.")
    doc.save(doc_path)
