import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["financial", "results", "earnings", "filing", "report", "quarter", "statement", "10-q", "10-k", "annual"]
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

def extract_tables_and_text(html):
    soup = BeautifulSoup(html, "lxml")
    try:
        tables = pd.read_html(str(soup))
    except Exception:
        tables = []
    return tables, soup.get_text()

def ai_extract_summary(text):
    prompt = f"""Summarize the main financial results and business highlights:

{text}"""
    try:
        key = st.secrets["together"]["api_key"]
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        res = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            return "Summary not available."
    except Exception:
        return "Summary failed to generate."

def generate_pdf(summaries):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Financial Summary Report", ln=True)
    pdf.set_font("Arial", size=11)
    for i, (url, content) in enumerate(summaries):
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 8, f"Page {i+1} - {url}")
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, content)
    path = "/mnt/data/financial_summary_report.pdf"
    pdf.output(path)
    return path

def run():
    st.title("Financial Data Extractor")

    url = st.text_input("Investor Relations URL")
    run_button = st.button("Summarize Company")
    show_tables = st.checkbox("Show financial tables (if available)", value=True)

    if run_button and url:
        with st.spinner("Scanning website..."):
            html = fetch_html(url)
            if not html:
                st.error("Failed to load the page.")
                return

            links = extract_financial_links(url, html)[:5]
            if not links:
                st.warning("No relevant subpages found.")
                return

            summaries = []

            for i, link in enumerate(links):
                sub_html = fetch_html(link)
                if not sub_html:
                    continue
                tables, text = extract_tables_and_text(sub_html)
                summary = ai_extract_summary(text)
                summaries.append((link, summary))

                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 1.2rem 1rem; margin-bottom: 2rem; border-radius: 6px; border: 1px solid #dee2e6'>
                    <h5 style='margin-bottom: 0.5rem;'>Page {i+1}</h5>
                    <div style='margin-bottom: 0.6rem;'>
                        <a href="{link}" target="_blank" style='font-weight: 500; text-decoration: none; color: #1a4c8c;'>View Original Page →</a>
                    </div>
                    <div style='padding: 0.6rem; background-color: #ffffff; border: 1px solid #ddd; border-radius: 4px; max-height: 300px; overflow-y: auto;'>
                        <p style='margin-bottom: 0.25rem; font-weight: 600;'>Summary:</p>
                        <div style='font-size: 0.92rem; line-height: 1.5;'>{summary.replace("\n", "<br>")}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if show_tables and tables:
                    st.markdown("**Extracted Table:**")
                    st.dataframe(tables[0], use_container_width=True)
                    st.markdown("---")

            if summaries:
                pdf_path = generate_pdf(summaries)
                with open(pdf_path, "rb") as f:
                    st.download_button("Download Summary as PDF", f, file_name="financial_summary_report.pdf", mime="application/pdf")
