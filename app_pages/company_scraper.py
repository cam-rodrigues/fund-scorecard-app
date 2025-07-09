import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from fpdf import FPDF

def extract_tables_from_url(url):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, "lxml")

        # Extract all HTML tables
        tables = pd.read_html(response.text)
        return tables, soup.get_text()
    except Exception as e:
        st.error(f"❌ Failed to load or parse page: {e}")
        return [], ""

def extract_key_metrics(text):
    metrics = {}
    keywords = [
        "revenue", "net income", "earnings per share", "eps", "ebitda", "gross margin", "operating income"
    ]
    lines = text.lower().splitlines()
    for kw in keywords:
        for line in lines:
            if kw in line and any(c.isdigit() for c in line):
                metrics[kw] = line.strip()
                break
    return metrics

def download_pdf(metrics, tables):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Company Financial Summary", ln=True)

    pdf.set_font("Arial", size=12)
    for key, val in metrics.items():
        pdf.cell(0, 10, f"{key.title()}: {val}", ln=True)

    pdf.output("/tmp/company_summary.pdf")
    return "/tmp/company_summary.pdf"

def run():
    st.title("🔎 Company Website Financial Scraper")
    st.markdown("Paste a **public company’s investor page** URL to extract tables and key financial metrics.")

    url = st.text_input("Enter company financial or investor website URL")

    if url:
        with st.spinner("Fetching and parsing the page..."):
            tables, text = extract_tables_from_url(url)
            metrics = extract_key_metrics(text)

        if metrics:
            st.success("✅ Found some key financial data:")
            for k, v in metrics.items():
                st.markdown(f"- **{k.title()}**: {v}")

        if tables:
            st.markdown("### 📊 Extracted Tables")
            for i, table in enumerate(tables[:3]):  # Limit to 3 tables for performance
                st.markdown(f"**Table {i + 1}:**")
                st.dataframe(table)

            csv = io.StringIO()
            tables[0].to_csv(csv, index=False)
            st.download_button("⬇️ Download First Table as CSV", csv.getvalue(), file_name="company_data.csv", mime="text/csv")

        if metrics:
            pdf_path = download_pdf(metrics, tables)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download Metrics PDF", f, file_name="company_summary.pdf", mime="application/pdf")

        if not tables and not metrics:
            st.warning("No usable financial tables or metrics found. Try a different investor relations page.")

