import streamlit as st
import pdfplumber
import fitz  # PyMuPDF for PDF rendering
import io
from utils.data_scanner import extract_fund_metrics  # Import from refactored logic
from utils.article_summarizer import summarize_article
from utils.pdf_generator import generate_summary_pdf

st.set_page_config(page_title="Article Analyzer", layout="wide")

st.title("Article Analyzer")
st.caption("Summarize financial articles and detect fund metrics (optional).")

# === Sidebar Controls ===
st.sidebar.header("Options")
enable_fund_detection = st.sidebar.checkbox("Enable Fund Metric Detection", value=True)
export_pdf = st.sidebar.button("Export Summary as PDF")

# === Input Source ===
input_mode = st.radio("Choose Input Method:", ["Paste Text", "Upload PDF"])
article_text = ""

if input_mode == "Paste Text":
    article_text = st.text_area("Paste Article Text Below", height=300)
elif input_mode == "Upload PDF":
    pdf_file = st.file_uploader("Upload a Financial News Article PDF", type=["pdf"])
    if pdf_file:
        with pdfplumber.open(pdf_file) as pdf:
            article_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# === Summary & Fund Extraction ===
if article_text.strip():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Summary")
        summary = summarize_article(article_text)
        st.write(summary)

    with col2:
        if enable_fund_detection:
            st.subheader("Detected Fund Metrics")
            metrics = extract_fund_metrics(article_text)
            if metrics:
                st.dataframe(metrics, use_container_width=True)
            else:
                st.info("No fund metrics detected.")
        else:
            st.info("Fund detection disabled.")

    # === Export Option ===
    if export_pdf:
        pdf_bytes = generate_summary_pdf(summary, metrics if enable_fund_detection else None)
        st.download_button("Download PDF", pdf_bytes, file_name="article_summary.pdf")

else:
    st.info("Paste text or upload a PDF to begin.")

# === Disclaimer ===
st.markdown("""
---
*This tool is for informational purposes only. Extracted metrics  may be incomplete or inaccurate.*
""")
