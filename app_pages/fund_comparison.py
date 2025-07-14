import streamlit as st
from io import BytesIO
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# === Generate a Simple Word Document ===
def generate_word_doc(summary_text):
    buffer = BytesIO()
    doc = Document()
    doc.add_heading("Proposal Summary", level=1)
    doc.add_paragraph(summary_text)
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# === Generate a Simple PDF ===
def generate_pdf(summary_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica", 12)
    for line in summary_text.split('\n'):
        c.drawString(50, y, line)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    return buffer

# === Streamlit App ===
st.set_page_config(page_title="Simple Export Tool")
st.title("📝 Export Summary")

# User input
st.subheader("Step 1: Write or paste your summary")
summary = st.text_area("Summary", height=200)

# Export option
st.subheader("Step 2: Choose file type")
file_type = st.radio("Export as:", ["Word (.docx)", "PDF (.pdf)"])

# Export button
if st.button("📥 Export Now"):
    if not summary.strip():
        st.warning("Please enter a summary first.")
    else:
        if file_type == "Word (.docx)":
            file = generate_word_doc(summary)
            st.download_button("Download DOCX", file, "Summary.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            file = generate_pdf(summary)
            st.download_button("Download PDF", file, "Summary.pdf", mime="application/pdf")
