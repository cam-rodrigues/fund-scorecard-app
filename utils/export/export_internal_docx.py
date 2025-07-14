from docx import Document

def export_internal_docx(df, proposal_html, file_obj):
    doc = Document()
    doc.add_heading("Internal Use Only", level=1)

    doc.add_paragraph("Detailed Proposal Analysis")
    doc.add_paragraph(proposal_html)

    # Add detailed table
    table = doc.add_table(rows=1, cols=len(df.columns))
    for i, col in enumerate(df.columns):
        table.rows[0].cells[i].text = col
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)

    doc.save(file_obj)
