import streamlit as st
import requests
from bs4 import BeautifulSoup
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

def safe_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")

def download_pdf(metrics):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Company Financial Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    for key, val in metrics.items():
        pdf.multi_cell(0, 10, safe_text(f"{key.title()}: {val}"))

    path = "/tmp/company_summary.pdf"
    pdf.output(path)
    return path

def run():
    st.title("📡 Company Financial Crawler")
    st.markdown("Enter an investor or financial site URL. FidSync will crawl subpages for financial data.")

    url = st.text_input("🔗 Enter company investor website")

    if url:
        with st.spinner("🔍 Crawling and parsing site..."):
            base_html = fetch_html(url)
            if not base_html:
                return

            subpage_urls = extract_financial_links(url, base_html)
            subpage_urls = list(dict.fromkeys(subpage_urls))[:15]

            if not subpage_urls:
                st.warning("No financial subpages found.")
                return

            st.info(f"🔗 Found {len(subpage_urls)} subpages. Scanning...")

            all_tables = []
            all_metrics = {}

            for sub_url in subpage_urls:
                if any(sub_url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                    st.warning(f"⚠️ Skipping non-HTML: {sub_url}")
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
                    st.error(f"❌ Error parsing {sub_url}: {e}")

        if all_metrics:
            st.success("✅ Key Financial Metrics Found")
            with st.expander("📌 View Metrics"):
                for k, v in all_metrics.items():
                    st.markdown(f"- **{k.title()}**: {v}")

        if all_tables:
            st.markdown("### 📊 Extracted Tables")
            for i, table in enumerate(all_tables[:3]):
                with st.expander(f"Table {i + 1}"):
                    st.dataframe(table)

            csv = io.StringIO()
            all_tables[0].to_csv(csv, index=False)
            st.download_button("⬇️ Download First Table as CSV", csv.getvalue(), file_name="company_data.csv", mime="text/csv")

        if all_metrics:
            pdf_path = download_pdf(all_metrics)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download Metrics PDF", f, file_name="company_summary.pdf", mime="application/pdf")

        if not all_tables and not all_metrics:
            st.warning("No financial data found.")
