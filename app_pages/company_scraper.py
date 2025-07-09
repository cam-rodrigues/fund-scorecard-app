import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from fpdf import FPDF
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = [
    "financial", "results", "earnings", "filing", "report",
    "quarter", "10-q", "10-k", "annual", "statement", "balance", "income"
]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

# === Fetching and Parsing ===
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

# === Metric Extraction & Cleaning ===
def clean_line_spacing(line):
    if len(line) > 10 and " " in line and any(c.isdigit() for c in line):
        spaced = re.sub(r"\s+", "", line)
        if spaced.isalnum():
            return spaced
    return line

def extract_key_metrics(text):
    groups = {
        "Profitability": ["net income", "ebitda", "adjusted ebitda", "earnings per share", "eps", "gross margin", "operating income"],
        "Liquidity": ["cash", "debt", "balance sheet"],
        "Distributions": ["dividend", "distribution"],
        "Revenue": ["revenue", "sales", "income statement"]
    }

    lines = text.lower().splitlines()
    cleaned_lines = [clean_line_spacing(l.strip()) for l in lines if any(c.isdigit() for c in l)]

    categorized = {"Profitability": [], "Liquidity": [], "Distributions": [], "Revenue": [], "Other": []}

    found = set()
    for line in cleaned_lines:
        matched = False
        for category, keywords in groups.items():
            for kw in keywords:
                if kw in line and kw not in found:
                    categorized[category].append((kw.title(), line.strip().capitalize()))
                    found.add(kw)
                    matched = True
                    break
            if matched:
                break
        if not matched and len(line.strip()) > 40:
            categorized["Other"].append(("", line.strip().capitalize()))

    return categorized

# === Safe PDF Output ===
def safe_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")

def download_pdf(metrics_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Company Financial Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    for group, items in metrics_dict.items():
        pdf.cell(0, 10, f"--- {group} ---", ln=True)
        for label, val in items:
            line = f"{label + ': ' if label else ''}{val}"
            pdf.multi_cell(0, 8, safe_text(line))
        pdf.ln(4)

    path = "/tmp/company_summary.pdf"
    pdf.output(path)
    return path

# === Streamlit App Logic ===
def run():
    st.title("📡 Company Financial Crawler")
    st.markdown("Enter an investor or financial site URL. FidSync will crawl subpages and extract metrics + tables.")

    url = st.text_input("🔗 Enter investor/financial website")

    if url:
        with st.spinner("🔍 Crawling site..."):
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
                    grouped = extract_key_metrics(text)
                    all_tables.extend(tables)
                    for cat, items in grouped.items():
                        if cat not in all_metrics:
                            all_metrics[cat] = []
                        all_metrics[cat].extend(items)
                except Exception as e:
                    st.error(f"❌ Error parsing {sub_url}: {e}")

        # === Metrics Output ===
        if any(all_metrics.values()):
            st.success("✅ Key Financial Metrics Found")

            view_mode = st.radio("How would you like to view metrics?", ["List View", "Table View"])

            if view_mode == "List View":
                for cat, items in all_metrics.items():
                    with st.expander(f"📂 {cat}"):
                        for label, val in items:
                            if label:
                                st.markdown(f"**{label}**")
                            st.markdown(f"> {val}")
            else:
                all_data = []
                for cat, items in all_metrics.items():
                    for label, val in items:
                        all_data.append((cat, label, val))
                df = pd.DataFrame(all_data, columns=["Category", "Metric", "Text"])
                st.dataframe(df)

        # === Table Output ===
        if all_tables:
            st.markdown("### 📊 Extracted Tables")
            for i, table in enumerate(all_tables[:3]):
                with st.expander(f"Table {i + 1}"):
                    st.dataframe(table)

            csv = io.StringIO()
            all_tables[0].to_csv(csv, index=False)
            st.download_button("⬇️ Download First Table as CSV", csv.getvalue(), file_name="company_data.csv", mime="text/csv")

        # === PDF Output ===
        if any(all_metrics.values()):
            pdf_path = download_pdf(all_metrics)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download Metrics PDF", f, file_name="company_summary.pdf", mime="application/pdf")

        if not all_tables and not any(all_metrics.values()):
            st.warning("No usable financial data found.")
