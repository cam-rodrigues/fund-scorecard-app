import streamlit as st
import pdfplumber
import re
from jinja2 import Template, StrictUndefined
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
        with pdfplumber.open(uploaded_file) as pdf:
            text = extract_pdf_text(pdf)
            fund_names = extract_fund_names_from_scorecard_pages(pdf)

        if not fund_names:
            st.warning("No fund names detected in 'Fund Scorecard' pages.")
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

            docx_bytes = generate_docx(writeup)
            pptx_bytes = generate_pptx_slide(writeup)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📄 Download as DOCX", docx_bytes, file_name="fund_writeup.docx")
            with col2:
                st.download_button("📊 Download as PPTX", pptx_bytes, file_name="fund_writeup.pptx")


# === Extract all PDF text ===
def extract_pdf_text(pdf):
    return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])


# === Extract fund names only from "Fund Scorecard" pages ===
def extract_fund_names_from_scorecard_pages(pdf):
    fund_names = set()
    for page in pdf.pages:
        text = page.extract_text()
        if not text or "Fund Scorecard" not in text:
            continue

        lines = text.splitlines()
        for line in lines:
            clean = line.strip()

            # Skip metric headers and diagnostic values
            if any(x in clean for x in [
                "Fund Scorecard", "Watchlist Criteria", "Sharpe", "Sortino", "Tracking Error", "Benchmark",
                "Peer Return", "Category", "Expense Ratio", "R-Squared", "Tenure", "Alpha", "Beta"
            ]):
                continue
            if len(clean) < 15 or clean.count(" ") < 2:
                continue
            if re.search(r"\d{4}|[%•]", clean):
                continue

            fund_names.add(clean)

    return sorted(fund_names)


# === Try to extract 5 return metrics near fund name ===
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


# === Generate formatted writeup ===
def generate_writeup(fund_name, manager, peer_rank, rec, metrics):
    template_str = """
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
""".strip()

    template = Template(template_str, undefined=StrictUndefined)
    return template.render(
        fund_name=fund_name,
        metrics=metrics,
        manager=manager,
        peer_rank=peer_rank,
        rec=rec
    )


# === DOCX Export ===
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


# === PPTX Export ===
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
