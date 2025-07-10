import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF
import os

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["financial", "results", "earnings", "filing", "report", "quarter"]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

def fetch_html(url):
    try:
        res = requests.get(url, timeout=10, headers=HEADERS)
        return res.text
    except Exception:
        return ""

def extract_financial_links(base_url, html):
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if any(kw in href.lower() for kw in KEYWORDS):
            full_url = href if href.startswith("http") else requests.compat.urljoin(base_url, href)
            if not any(full_url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                links.add(full_url)
    return list(links)

def extract_visible_text(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def ai_summarize_text(text):
    # Simulated AI output — replace with real API logic
    if "2025 Q1" in text:
        return """**Financial Results:**

* Net earnings: $70 million  
* Adjusted net earnings: $70 million  
* Adjusted EBITDA: $353 million  
* Cash and cash equivalents: $361 million  
* Total debt: $1.0 billion  
* Undrawn credit facility: $1.0 billion

**Business Highlights:**

* Strong operational performance  
* Increased long-term contract portfolio  
* Continued positive market momentum"""
    return ""

def generate_pdf_report(summaries):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Financial Summary Report", ln=True)

    pdf.set_font("Arial", "", 12)
    for i, (url, summary) in enumerate(summaries, 1):
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Page {i}: {url}", ln=True)
        pdf.set_font("Arial", "", 11)
        for line in summary.split("\n"):
            pdf.multi_cell(0, 8, line)

    path = "/mnt/data/financial_summary_report.pdf"
    pdf.output(path)
    return path

def run():
    st.markdown("""
        <h1 style='font-size:2.2rem; margin-bottom:0.5rem;'>Company Financial Insights</h1>
        <p style='color:gray; font-size:0.9rem;'>Summarize financial data and key metrics from investor pages.</p>
    """, unsafe_allow_html=True)

    url = st.text_input("Investor Website URL")
    show_tables = st.checkbox("Show financial tables (if available)", value=True)
    summarize = st.button("Summarize Company")

    if summarize and url:
        with st.spinner("Scanning website..."):
            base_html = fetch_html(url)
            subpages = extract_financial_links(url, base_html)

            if not subpages:
                st.warning("No subpages found with financial keywords.")
                return

            summaries = []
            for i, link in enumerate(subpages, 1):
                st.markdown(f"<h4>Page {i}</h4>", unsafe_allow_html=True)
                st.markdown(f"<a href='{link}' target='_blank' style='text-decoration:none; color:#1658c8;'>View Original Page ➜</a>", unsafe_allow_html=True)

                sub_html = fetch_html(link)
                raw_text = extract_visible_text(sub_html)
                summary = ai_summarize_text(raw_text)

                if summary:
                    st.markdown(f"**Summary:**\n\n{summary}", unsafe_allow_html=True)
                    summaries.append((link, summary))
                else:
                    st.markdown("*No summary available.*", unsafe_allow_html=True)

                if show_tables:
                    try:
                        tables = pd.read_html(sub_html)
                        if tables:
                            st.dataframe(tables[0])
                    except Exception:
                        pass

            if summaries:
                pdf_path = generate_pdf_report(summaries)
                with open(pdf_path, "rb") as f:
                    st.download_button("Download Summary as PDF", f, file_name="financial_summary_report.pdf", mime="application/pdf")

