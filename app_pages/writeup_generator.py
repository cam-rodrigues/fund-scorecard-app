import streamlit as st
import pdfplumber
import re
import textwrap
from jinja2 import Template
from io import BytesIO
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor


def run():
    st.set_page_config(page_title="Fund Writeup Generator", layout="wide")
    st.title("📄 Fund Writeup Generator")

    st.markdown("Upload an MPI-style PDF and generate a client-ready writeup.")

    uploaded_file = st.file_uploader("Upload MPI-style PDF", type=["pdf"])

    if uploaded_file:
        text = extract_pdf_text(uploaded_file)
        fund_names = extract_fund_names(text)

        if not fund_names:
            st.warning("No fund names detected. Try uploading a different PDF.")
            return

        with st.form("writeup_form"):
            fund_name = st.selectbox("Select a fund", fund_names)
            manager = st.text_input("Manager Name", value="Phil Ruvinsky")
            peer_rank = st.selectbox("Peer Rank", ["Top Quartile", "Middle Quartile", "Bottom Quartile"])
            rec = st.selectbox("Recommendation", ["Recommended", "Watchlist", "Replace", "Hold"])
            submit = st.form_submit_button("Generate Writeup")

        if submit:
            metrics = extract_sample_metrics(text, fund_name)
            writeup = generate_writeup(fund_name, manager, peer_rank, rec, metrics)

            st.markdown("---")
            st.subheader("📋 Writeup Preview")
            st.markdown(writeup)

            # Export options
            docx_bytes = generate_docx(writeup)
            pptx_bytes = generate_pptx_slide(writeup)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📄 Download as DOCX", docx_bytes, file_name="fund_writeup.docx")
            with col2:
                st.download_button("📊 Download as PPTX", pptx_bytes, file_name="fund_writeup.pptx")


# === PDF extraction ===
def extract_pdf_text(file_obj):
    with pdfplumber.open(file_obj) as pdf:
        return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])


def extract_fund_names(text):
    # Match long names followed by returns (%)
    lines = text.splitlines()
    fund_names = set()
    for line in lines:
        if re.search(r"[A-Za-z]{4,}.*?(-?\d+\.\d+%)", line):
            name = line.strip()
            if len(name.split()) >= 3:
                fund_names.add(name.split("  ")[0].strip())  # remove trailing returns
    return sorted(fund_names)


def extract_sample_metrics(text, fund_name):
    pattern = rf"{re.escape(fund_name)}.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return {
            "qtd": match.group(1),
            "1yr": match.group(2),
            "3yr": match.group(3),
            "5yr": match.group(4),
            "10yr": match.group(5)
        }
    return {k: "N/A" for k in ["qtd", "1yr", "3yr", "5yr", "10yr"]}


def generate_writeup(fund_name, manager, peer_rank, rec, metrics):
    template_str = textwrap.dedent("""
        ### {{ fund_name }}

        **Performance Summary**
        - QTD: {{ metrics["qtd"] }}%
        - 1YR: {{ metrics["1yr"] }}%
        - 3YR: {{ metrics["3yr"] }}%
        - 5YR: {{ metrics["5yr"] }}%
        - 10YR: {{ metrics["10yr"] }}%

        **Manager & Strategy**
        Managed by **{{ manager }}**, this fund has demonstrated performance {{ peer_rank }} relative to its peers.

        **Recommendation**
        **Action:** {{ rec }}
    """)
    return Template(template_str).render(
        fund_name=fund_name,
        metrics=metrics,
        manager=manager,
        peer_rank=peer_rank,
        rec=rec
    )


# === Exporters ===
def generate_docx(writeup_text):
    doc = Document()
    doc.add_heading('Fund Writeup', 0)
    for line in writeup_text.split("\n"):
        if line.startswith("### "):
            doc.add_heading(line.replace("### ", ""), level=1)
        elif line.startswith("**") and line.endswith("**"):
            doc.add_heading(line.replace("**", ""), level=2)
        else:
            doc.add_paragraph(line.replace("**", ""))
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def generate_pptx_slide(writeup_text):
    prs = Presentation()
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    left, top, width, height = Inches(0.5), Inches(0.3), Inches(9), Inches(6.5)
    textbox = slide.shapes.add_textbox(left, top, width, height)
    tf = textbox.text_frame

    for line in writeup_text.split("\n"):
        if not line.strip():
            continue
        p = tf.add_paragraph()
        p.text = line.replace("**", "").replace("### ", "")
        p.font.size = Pt(16)
        p.font.name = 'Arial'
        p.font.color.rgb = RGBColor(30, 30, 30)
    tf.paragraphs[0].font.size = Pt(22)
    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf
