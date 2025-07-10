import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF
import os

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["financial", "results", "earnings", "filing", "report", "quarter", "summary"]
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

def extract_tables(text):
    try:
        return pd.read_html(text)
    except Exception:
        return []

def generate_pdf(summaries):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Company Financial Summary", ln=True)
    pdf.set_font("Arial", size=11)

    for page_num, content in summaries.items():
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Page {page_num}", ln=True)
        pdf.set_font("Arial", size=11)
        lines = content.replace("**", "").replace("*", "").splitlines()
        for line in lines:
            pdf.multi_cell(0, 8, line.strip())
        pdf.ln(5)

    pdf_path = "/mnt/data/financial_summary_report.pdf"
    pdf.output(pdf_path)
    return pdf_path

def summarize_text(text):
    # Basic keyword matcher to simulate financial summary
    lines = text.splitlines()
    summary_lines = [line for line in lines if any(kw in line.lower() for kw in KEYWORDS) and any(c.isdigit() for c in line)]
    return "\n".join(summary_lines[:15])

def run():
    st.title("Company Financial Data Extractor")
    st.caption("Summarize company investor pages and download financial summaries.")

    url = st.text_input("Enter investor/financial website", placeholder="https://example.com")

    filter_toggle = st.toggle("Show financial tables (if available)", value=True)

    if st.button("Summarize Company") and url:
        with st.spinner("🔎 Scanning website..."):
            html = fetch_html(url)
            links = extract_financial_links(url, html)

        if not links:
            st.warning("No financial subpages found.")
            return

        st.info(f"Found {len(links)} financial subpages.")

        summaries = {}
        for i, link in enumerate(links):
            st.markdown(f"### Page {i+1}")
            st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;color:#1a5cff;">View Original Page →</a>', unsafe_allow_html=True)

            html = fetch_html(link)
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(separator="\n")
            summary = summarize_text(text)

            if summary:
                formatted = f"**Summary:**\n\nHere are the main financial results and business highlights from the page:\n\n" + summary
                st.markdown(formatted, unsafe_allow_html=True)
                summaries[i + 1] = formatted
            else:
                st.warning("No financial metrics detected on this page.")

            if filter_toggle:
                tables = extract_tables(html)
                for idx, table in enumerate(tables[:1]):  # Just show one per page max
                    st.markdown(f"**Extracted Table {idx+1}:**")
                    st.dataframe(table)

        if summaries:
            pdf_path = generate_pdf(summaries)
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button("Download Summary as PDF", f, file_name="financial_summary_report.pdf", mime="application/pdf")
            else:
                st.error("PDF could not be generated. Try refreshing the app.")

