# app_pages/article_analyzer.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from fpdf import FPDF
import re
from datetime import datetime

def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove obvious junk tags
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        # Collect all <p> tags
        paragraphs = soup.find_all("p")
        text_lines = [p.get_text().strip() for p in paragraphs]
        text_lines = [line for line in text_lines if len(line) > 40]

        cleaned = "\n".join(text_lines)

        # Loosen success check — if it has 3+ long paragraphs, allow it
        if len(text_lines) >= 3 and len(cleaned) > 250:
            return cleaned
        else:
            return "ERROR: Not enough useful content found."

    except Exception as e:
        return f"ERROR: {e}"

def extract_date(text):
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}", text)
    return match.group(0) if match else None

def extract_main_idea(text):
    lines = text.split("\n")
    for line in lines:
        if len(line.split()) > 10 and line[-1] in ".!?":
            return line.strip()
    return lines[0] if lines else "N/A"

def extract_key_points(text, count=5):
    sentences = re.split(r'(?<=[.?!])\s+', text)
    clean = [s.strip() for s in sentences if len(s) > 60 and not any(
        kw in s.lower() for kw in ["subscribe", "sign up", "free", "fiduciary", "advertise"]
    )]
    ranked = sorted(clean, key=len, reverse=True)
    return ranked[:count]

def extract_quotes(text):
    return re.findall(r'“([^”]{20,})”', text) or re.findall(r'"([^"]{20,})"', text)

def export_to_pdf(summary_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Article Summary", ln=1)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, f"URL: {summary_data['url']}\n")

    if summary_data.get("date"):
        pdf.cell(0, 10, f"Date: {summary_data['date']}", ln=1)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Main Idea:", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, summary_data['main_idea'] + "\n")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Key Points:", ln=1)
    pdf.set_font("Arial", "", 11)
    for point in summary_data['key_points']:
        pdf.multi_cell(0, 8, f"• {point}")

    if summary_data['quotes']:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Notable Quotes:", ln=1)
        pdf.set_font("Arial", "I", 11)
        for quote in summary_data['quotes'][:3]:
            pdf.multi_cell(0, 8, f"“{quote}”")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def run():
    st.title("🔎 Article Analyzer")
    st.markdown("Paste a finance article URL. We'll extract the main idea, key points, quotes, and give you a downloadable PDF.")

    url = st.text_input("Paste article URL here")

    bullet_count = st.slider("How many key points?", min_value=3, max_value=10, value=5)

    if st.button("Analyze Article"):
        if not url:
            st.warning("Please paste a URL.")
            return

        with st.spinner("Fetching and analyzing..."):
            full_text = extract_article_text(url)

        if full_text.startswith("ERROR:") or len(full_text.strip()) < 100:
            st.error("❌ Failed to extract meaningful article content.")
            return

        summary = {
            "url": url,
            "date": extract_date(full_text),
            "main_idea": extract_main_idea(full_text),
            "key_points": extract_key_points(full_text, bullet_count),
            "quotes": extract_quotes(full_text),
        }

        st.subheader("🧠 Main Idea")
        st.write(summary['main_idea'])

        if summary['date']:
            st.subheader("📅 Date")
            st.write(summary['date'])

        st.subheader("📌 Key Points")
        for i, point in enumerate(summary['key_points'], 1):
            st.markdown(f"**{i}.** {point}")

        if summary['quotes']:
            st.subheader("💬 Notable Quotes")
            for quote in summary['quotes'][:3]:
                st.markdown(f"> {quote}")

        # PDF download
        pdf_bytes = export_to_pdf(summary)
        st.download_button("📄 Download PDF", data=pdf_bytes, file_name="article_summary.pdf", mime="application/pdf")
