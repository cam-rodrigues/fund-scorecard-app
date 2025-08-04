import streamlit as st
import pdfplumber
import re
import pandas as pd
from newspaper import Article
from fpdf import FPDF
import tempfile
import os

# === Article Summarizer ===
def summarize_article(text):
    return text[:1000] + "..." if len(text) > 1000 else text

# === PDF Export Function ===
def export_summary_to_pdf(summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="Article Summary", align='L')
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=summary)
    temp_path = os.path.join(tempfile.gettempdir(), "summary.pdf")
    pdf.output(temp_path)
    return temp_path

# === Main Streamlit App ===
def main():
    st.set_page_config(page_title="Article Analyzer", layout="wide")
    st.markdown("""
    <style>
    .input-card, .summary-card {
        background: #f7fafd;
        border: 1.2px solid #d6e1f3;
        border-radius: 1.3rem;
        box-shadow: 0 2px 8px rgba(66,120,170,0.08);
        padding: 2rem 2.4rem 1.7rem 2.4rem;
        margin-bottom: 2.1rem;
    }
    .summary-card {
        border: 1.5px solid #a8c2e2;
        background: #f4f8fd;
        margin-top: 1.4rem;
    }
    .summary-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #214a7d;
        margin-bottom: 0.8em;
        margin-top: 0.1em;
    }
    .button-bar {
        margin-top: 1.2rem;
        margin-bottom: 0.3rem;
    }
    .stDownloadButton > button {
        background: #2562b3 !important;
        color: #fff !important;
        border-radius: 1.2rem !important;
        padding: 0.44rem 1.6rem !important;
        font-weight: 700 !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Article Analyzer")
    st.caption("Paste a URL, upload a PDF, or input text to get a clean article summary.")

    with st.container():
        st.markdown('<div class="input-card">', unsafe_allow_html=True)

        input_mode = st.selectbox("Choose Article Input Method", ["Paste URL", "Paste Text", "Upload PDF"])
        article_text = ""

        if input_mode == "Paste URL":
            url = st.text_input("Enter Article URL")
            if url:
                try:
                    article = Article(url)
                    article.download()
                    article.parse()
                    article_text = article.text
                except Exception as e:
                    st.error(f"Failed to fetch article: {e}")

        elif input_mode == "Paste Text":
            article_text = st.text_area("Paste the Full Article Text Below", height=300)

        elif input_mode == "Upload PDF":
            pdf_file = st.file_uploader("Upload PDF File", type=["pdf"])
            if pdf_file:
                with pdfplumber.open(pdf_file) as pdf:
                    article_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

        st.markdown('</div>', unsafe_allow_html=True)

    if article_text.strip():
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown('<div class="summary-title">Summary</div>', unsafe_allow_html=True)
        summary = summarize_article(article_text)
        st.write(summary)

        st.markdown('<div class="button-bar">', unsafe_allow_html=True)
        if st.button("Export Summary as PDF"):
            pdf_path = export_summary_to_pdf(summary)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="article_summary.pdf",
                    mime="application/pdf"
                )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("<hr style='margin-top:2.2rem; margin-bottom:0.6rem; border-top:1.2px solid #d6e1f3;'>", unsafe_allow_html=True)
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")

# === Required for Multipage Setup ===
def run():
    main()
