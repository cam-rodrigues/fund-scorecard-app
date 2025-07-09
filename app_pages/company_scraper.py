import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import io
from fpdf import FPDF

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = [
    "financial", "results", "earnings", "filing", "report",
    "quarter", "10-q", "10-k", "annual", "statement", "balance", "income"
]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

def fetch_html(url):
    try:
        res = requests.get(url, timeout=10, headers=HEADERS)
        return res.text
    except Exception as e:
        st.error(f"❌ Failed to fetch {url}: {e}")
        return ""

def extract_financial_links(base_url, html):
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if any(kw in href.lower() for kw in KEYWORDS):
            full_url = href if href.startswith("http") else requests.compat.urljoin(base_url, href)
            links.add(full_url)
    return list(links)

def extract_tables_and_text(html):
    soup = BeautifulSoup(html, "lxml")
    try:
        tables = pd.read_html(str(soup))
    except Exception:
        tables = []
    return tables, soup.get_text()

def extract_key_metrics(text):
    metrics = {}
    keywords = [
        "revenue", "net income", "earnings per share", "eps",
        "ebitda", "gross margin", "operating income"
    ]
    lines = text.lower().splitlines()
    for kw in keywords:
        for line in lines:
            if kw in line and any(c.isdigit() for c in line):
                metrics[kw] = line.strip()
                break
    return metrics

def download_pdf(metrics, all_tables):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Aggregated Company Financial Summary", ln=True)
    pdf.set_font("Arial", size=12)
    for key, val in metrics.items():
        pdf.cell(0, 10, f"{key.title()}: {val}", ln=True)
    pdf.output("/tmp/company_summary.pdf")
    return "/tmp/company_summary.pdf"

def run():
    st.title("🔎 Multi-Page Company Financial Crawler")
    st.markdown("Enter a **company investor or financial site URL**. The tool will crawl linked subpages that mention financials, filings, reports, etc.")

    url = st.text_input("Enter investor/financial website URL")

    if url:
        with st.spinner("🔍 Scanning the homepage and subpages..."):
            base_html = fetch_html(url)
            if not base_html:
                return

            subpage_urls = extract_financial_links(url, base_html)
            subpage_urls = list(dict.fromkeys(subpage_urls))[:10]
            st.info(f"🔗 Found {len(subpage_urls)} financial subpages to scan.")

            all_tables = []
            all_metrics = {}

            for sub_url in subpage_urls:
                if any(sub_url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                    st.warning(f"⚠️ Skipping non-HTML page: {sub_url}")
                    continue

                st.markdown(f"**Scanning:** {sub_url}")
                sub_html = fetch_html(sub_url)
                if not sub_html:
                    continue

                try:
                    tables, text = extract_tables_and_text(sub_html)
                    metrics = extract_key_metrics(text)
                    all_tables.extend(tables)
                    all_metrics.update(metrics)
                except Exception as e:
                    st.error(f"❌ Failed to load page: {e}")

        if all_metrics:
            st.success("✅ Aggregated Key Financial Metrics:")
            for k, v in all_metrics.items():
                st.markdown(f"- **{k.title()}**: {v}")

        if all_tables:
            st.markdown("### 📊 Extracted Tables (first 3 shown)")
            for i, table in enumerate(all_tables[:3]):
                st.markdown(f"**Table {i + 1}:**")
                st.dataframe(table)

            csv = io.StringIO()
            all_tables[0].to_csv(csv, index=False)
            st.download_button("⬇️ Download First Table as CSV", csv.getvalue(), file_name="company_data.csv", mime="text/csv")

        if all_metrics:
            pdf_path = download_pdf(all_metrics, all_tables)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download Metrics PDF", f, file_name="company_summary.pdf", mime="application/pdf")

        if not all_tables and not all_metrics:
            st.warning("No financial content found on this domain.")
