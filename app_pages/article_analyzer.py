# app_pages/article_analyzer.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from fpdf import FPDF
import re

def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove common noise
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        # Try to use <article> tag first
        paragraphs = []
        if (article_tag := soup.find("article")):
            paragraphs = article_tag.find_all("p")
        else:
            # Fallback: scan all <p> tags on the page
            paragraphs = soup.find_all("p")

        lines = [p.get_text().strip() for p in paragraphs]
        lines = [line for line in lines if len(line) > 60 and not any(
            kw in line.lower() for kw in ["sign up", "subscribe", "cookie", "ad blocker", "advertisement"]
        )]

        cleaned_text = "\n".join(lines)
        return cleaned_text if len(cleaned_text) > 200 else "ERROR: Not enough useful content found."
    except Exception as e:
        return f"ERROR: {e}"


def summarize_text(text, bullet_count):
    # Basic naive summary: longest N lines that look meaningful
    sentences = re.split(r'(?<=[.?!])\s+', text)
    ranked = sorted(sentences, key=lambda s: len(s), reverse=True)
    return ranked[:bullet_count]

def export_to_pdf(title, url, bullets):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Article Summary", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, f"URL: {url}\n", ln=True)

    for i, bullet in enumerate(bullets, 1):
        pdf.multi_cell(0, 8, f"• {bullet.strip()}\n")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def run():
    st.title("🔗 Article Analyzer")
    st.markdown("Paste a finance article URL, choose how many key points you want, and download a clean PDF summary.")

    url = st.text_input("Paste article URL here")

    bullet_count = st.slider("How many bullet points?", min_value=3, max_value=10, value=5)

    if st.button("Analyze Article"):
        if not url:
            st.warning("Please paste a URL first.")
            return

        with st.spinner("Fetching and analyzing..."):
            article_text = extract_article_text(url)

        if article_text.startswith("ERROR:") or len(article_text.strip()) < 100:
            st.error("Failed to extract meaningful article content.")
            return

        summary = summarize_text(article_text, bullet_count)

        st.subheader("📌 Summary")
        for i, bullet in enumerate(summary, 1):
            st.markdown(f"**{i}.** {bullet.strip()}")

        # PDF Export
        pdf_bytes = export_to_pdf("Article Summary", url, summary)
        st.download_button("📄 Download PDF", data=pdf_bytes, file_name="summary.pdf", mime="application/pdf")
