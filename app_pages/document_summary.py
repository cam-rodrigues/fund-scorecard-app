import streamlit as st
import pdfplumber
from docx import Document
import re
import pandas as pd

# -------------------------
# File Extraction
# -------------------------

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            return "\n".join([page.extract_text() or "" for page in pdf.pages])
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    return None

# -------------------------
# Heading-Based Summary
# -------------------------

def extract_headings_summary(text, lines_per_section=3):
    lines = text.splitlines()
    summary = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if (line.isupper() and len(line) > 5) or re.match(r'^([A-Z][a-z]+ ){1,5}[A-Z][a-z]+$', line) or line.endswith(":"):
            section = [f"### {line}"]
            for j in range(1, lines_per_section + 1):
                if i + j < len(lines):
                    content_line = lines[i + j].strip()
                    if content_line:
                        section.append(f"- {content_line}")
            summary.append("\n".join(section))
            i += lines_per_section
        i += 1
    return "\n\n".join(summary)

# -------------------------
# Table Analysis
# -------------------------

def analyze_metrics(df):
    analysis = []
    numeric_cols = df.select_dtypes(include="number").columns

    for col in numeric_cols:
        max_row = df.loc[df[col].idxmax()]
        min_row = df.loc[df[col].idxmin()]

        analysis.append(f"**Highest {col}**: {max_row['Fund']} ({max_row[col]})")
        analysis.append(f"**Lowest {col}**: {min_row['Fund']} ({min_row[col]})")
        analysis.append("")  # spacer

    return "\n".join(analysis)

# -------------------------
# Streamlit UI
# -------------------------

def run():
    st.markdown("## 📄 Document Summary Tool")
    st.markdown("Upload a `.pdf`, `.docx`, or `.txt` to extract a summary based on headings.")

    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])
    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)

        if not raw_text:
            st.error("Failed to extract text from file.")
            return

        with st.expander("🔍 Preview Extracted Text"):
            st.code(raw_text[:1000])

        st.markdown("### 🧠 Structured Summary")
        summary = extract_headings_summary(raw_text)
        if summary.strip():
            st.markdown(summary)
        else:
            st.warning("No clear headings found.")

    # --- Simulated Table Analyzer ---
    st.markdown("---")
    st.markdown("## 📊 Simulated Metric Table Analysis")
    st.markdown("Paste a CSV-like table below to analyze fund metrics:")

    sample_input = """Fund,Ticker,Alpha,Beta,Tracking Error,R-Squared
Vanguard 2025,VTTWX,0.38,1.08,2.49,96.74
Vanguard 2050,VFIAX,-0.32,0.92,3.57,94.99
Vanguard 2065+,VLXVX,-0.38,0.88,4.02,94.38"""

    table_input = st.text_area("Paste fund metric table here:", value=sample_input, height=200)
    if st.button("Analyze Table"):
        try:
            df = pd.read_csv(pd.compat.StringIO(table_input))
            st.dataframe(df)
            st.markdown("### 🔎 Metric Analysis")
            st.markdown(analyze_metrics(df))
        except Exception as e:
            st.error(f"Failed to parse table: {e}")
