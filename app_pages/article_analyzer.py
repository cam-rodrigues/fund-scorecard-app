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

    st.title("Article Analyzer")
    st.caption("Paste a URL, upload a PDF, or input text to get a clean article summary.")

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

    if article_text.strip():
        st.subheader("Summary")
        summary = summarize_article(article_text)
        st.write(summary)

        # PDF export
        if st.button("Export Summary as PDF"):
            pdf_path = export_summary_to_pdf(summary)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="article_summary.pdf",
                    mime="application/pdf"
                )


    # Disclaimer
    st.markdown("---")
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")
# === Required for Multipage Setup ===
def run():
    main()
