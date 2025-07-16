import streamlit as st
import pdfplumber
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from docx import Document
from io import BytesIO

st.set_page_config(page_title="Writeup Generator", layout="wide")
st.title("Writeup Generator")

# === Upload PDF ===
pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
if not pdf_file:
    st.stop()

# === Extract Text Blocks from Scorecard Pages Only ===
@st.cache_data(show_spinner=False)
def extract_fund_blocks(pdf_bytes):
    fund_blocks = []
    fund_name_pattern = re.compile(r"[A-Z][A-Za-z0-9 ,\-&]{4,} Fund")
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "FUND SCORECARD" in text.upper():
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    if fund_name_pattern.search(line):
                        block = "\n".join(lines[i : i + 12])
                        fund_blocks.append(block)
    return fund_blocks

fund_blocks = extract_fund_blocks(pdf_file)

# === Extract Valid Fund Names ===
fund_names = []
fund_block_map = {}
for block in fund_blocks:
    match = re.search(r"([A-Z][A-Za-z0-9 ,\-&]{4,} Fund)", block)
    if match:
        name = match.group(1).strip()
        fund_names.append(name)
        fund_block_map[name] = block

if not fund_names:
    st.warning("No valid funds found in scorecard pages.")
    st.stop()

selected_fund = st.selectbox("Select a Fund", fund_names)
if not selected_fund:
    st.stop()

block = fund_block_map[selected_fund]

# === Generate Writeup Content ===
def build_writeup_text(name, block):
    lines = [
        "**Recommendation Summary**",
        "",
        f"We reviewed the available funds and recommend **{name}** as a potential primary candidate based on key performance indicators:",
        "",
        "**Trailing Returns (Extracted Sample):**",
        "",
        block,
        "",
        "**Considerations:**",
        "- Strong performance across long-term periods",
        "- Low expense ratio compared to peers",
        "- Solid category ranking and consistency",
        "",
        "This recommendation should be confirmed against current plan goals, investment policy benchmarks, and fiduciary guidelines."
    ]
    return "\n".join(lines)

writeup = build_writeup_text(selected_fund, block)

# === Preview Writeup ===
st.subheader("Writeup Preview")
st.markdown(writeup)

# === DOCX Export ===
def export_docx(name, writeup):
    doc = Document()
    doc.add_heading(f'Proposal: {name}', 0)
    for line in writeup.split("\n"):
        doc.add_paragraph(line)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# === PPTX Export (Mimicking Slide Format) ===
def export_pptx(name, writeup):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout

    # Title box
    title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.3), Inches(9), Inches(1))
    title_tf = title_box.text_frame
    title_run = title_tf.paragraphs[0].add_run()
    title_run.text = f"Recommendation: {name}"
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0, 32, 96)

    # Body
    body_box = slide.shapes.add_textbox(Inches(0.3), Inches(1.3), Inches(9), Inches(5.5))
    body_tf = body_box.text_frame
    for line in writeup.split("\n"):
        if line.strip():
            p = body_tf.add_paragraph()
            p.text = line.strip()
            p.level = 0

    bio = BytesIO()
    prs.save(bio)
    return bio.getvalue()

# === Export Buttons ===
st.download_button("📄 Export as DOCX", export_docx(selected_fund, writeup), file_name=f"{selected_fund}_proposal.docx")
st.download_button("📊 Export as PPTX", export_pptx(selected_fund, writeup), file_name=f"{selected_fund}_slide.pptx")
