import streamlit as st
import pdfplumber
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from docx import Document
from docx.shared import Inches as DocxInches
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
                        block = "\n".join(lines[i : i + 12])  # extract ~12 lines
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
    return f"""
**Recommendation Summary**

We reviewed the available funds and recommend **{name}** as a potential primary candidate based on key performance indicators:

- **Trailing Returns (Extracted Sample):**
