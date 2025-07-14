from docx import Document
from bs4 import BeautifulSoup

def export_internal_docx(df, proposal_html, file_obj):
    doc = Document()

    # Title
    doc.add_heading("Internal Proposal", level=1)
    doc.add_paragraph("Detailed Analysis")

    # Clean the HTML from proposal text
    soup = BeautifulSoup(proposal_html, "html.parser")
    clean_text = soup.get_text()
    doc.add_paragraph(clean_text)

    # Add Scorecard Table
    if not df.empty:
        table = doc.add_table(rows=1, cols=len(df.columns))
        table.style = 'Light Grid'

        # Header row
        hdr_cells = table.rows[0].cells
        for i, col in enumerate(df.columns):
            hdr_cells[i].text = str(col)

        # Data rows
        for _, row in df.iterrows():
            row_cells = table.add_row().cells
            for i, val in enumerate(row):
                row_cells[i].text = str(val)

    # Export to provided file_obj (BytesIO or path)
    doc.save(file_obj)
