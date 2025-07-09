import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from fpdf import FPDF
import re
import string

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = [
    "financial", "results", "earnings", "filing", "report",
    "quarter", "10-q", "10-k", "annual", "statement", "balance", "income"
]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

ENGLISH_WORDS = set("""
the of and a to in is you that it he was for on are as with his they i at be this have from or one had by word
but not what all were we when your can said there use an each which she do how their if will up other about out
many then them these so some her would make like him into time has look two more write go see number no way could
people my than first water been call who oil its now find long down day did get come made may part back our over new
sound take only little work know place years live me most very after thing give name good sentence man think say great
where help through much before line right too means old any same tell boy follow came want show also around form three
small set put end does another well large must big even such because turn here why ask went men read need land different
home us move try kind hand picture again change off play spell air away animal house point page letter mother answer found
study still learn should america world high every near add food between own below country plant last school father keep tree
never start city earth eye light thought head under story saw left don't few while along might close something seem next hard
open example begin life always those both paper together got group often run important until children side feet car mile night
walk white sea began grow took river four carry state once book hear stop without second later miss idea enough eat face watch
""".split())

def is_mostly_english(text, threshold=0.3):
    words = text.translate(str.maketrans('', '', string.punctuation)).split()
    if not words:
        return False
    match_count = sum(1 for word in words if word.lower() in ENGLISH_WORDS)
    return match_count / len(words) >= threshold

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

def clean_line_spacing(line):
    if len(line) > 10 and " " in line and any(c.isdigit() for c in line):
        spaced = re.sub(r"\s+", "", line)
        if spaced.isalnum():
            return spaced
    return line

def extract_key_metrics(text, custom_keywords=None, show_debug=False):
    all_keywords = custom_keywords if custom_keywords else [
        "net income", "ebitda", "adjusted ebitda", "earnings per share", "eps",
        "gross margin", "operating income", "cash", "debt", "dividend",
        "distribution", "revenue", "sales", "income statement"
    ]

    groups = {
        "Profitability": ["net income", "ebitda", "adjusted ebitda", "earnings per share", "eps", "gross margin", "operating income"],
        "Liquidity": ["cash", "debt", "balance sheet"],
        "Distributions": ["dividend", "distribution"],
        "Revenue": ["revenue", "sales", "income statement"]
    }

    lines = text.lower().splitlines()
    cleaned_lines = [
        clean_line_spacing(l.strip())
        for l in lines
        if any(c.isdigit() for c in l) and is_mostly_english(l.strip())
    ]

    if show_debug:
        rejected = [
            l.strip() for l in lines
            if any(c.isdigit() for c in l)
            and not is_mostly_english(l.strip())
        ]
        st.expander("🔍 Filtered (rejected) lines").write(rejected[:50])

    categorized = {"Profitability": [], "Liquidity": [], "Distributions": [], "Revenue": [], "Other": []}
    found = set()

    for line in cleaned_lines:
        matched = False
        for category, keywords in groups.items():
            for kw in keywords:
                if kw in line and kw not in found and kw in all_keywords:
                    categorized[category].append((kw.title(), line.strip().capitalize()))
                    found.add(kw)
                    matched = True
                    break
            if matched:
                break
        if not matched and any(kw in line for kw in all_keywords):
            categorized["Other"].append(("", line.strip().capitalize()))

    return categorized

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
        pdf.ln(2)

    path = "/tmp/company_summary.pdf"
    pdf.output(path)
    return path

def run():
    st.title("📡 Company Financial Crawler")
    st.markdown("Enter a URL. FidSync will crawl linked subpages and extract clean financial metrics.")

    url = st.text_input("🔗 Enter investor/financial website")

    common_terms = [
        "net income", "ebitda", "adjusted ebitda", "eps", "gross margin", "revenue",
        "operating income", "dividend", "distribution", "debt", "cash", "income statement", "sales"
    ]
    selected_terms = st.multiselect("🔎 Optional: Filter for specific financial terms", common_terms)

    show_debug = st.checkbox("🧪 Show filtered (rejected) lines", value=False)

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
                    grouped = extract_key_metrics(text, selected_terms, show_debug)
                    all_tables.extend(tables)
                    for cat, items in grouped.items():
                        if cat not in all_metrics:
                            all_metrics[cat] = []
                        all_metrics[cat].extend(items)
                except Exception as e:
                    st.error(f"❌ Error parsing {sub_url}: {e}")

        if any(all_metrics.values()):
            st.success("✅ Cleaned Financial Metrics Extracted")

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

        if all_tables:
            st.markdown("### 📊 Extracted Tables")
            for i, table in enumerate(all_tables[:3]):
                with st.expander(f"Table {i + 1}"):
                    st.dataframe(table)

            csv = io.StringIO()
            all_tables[0].to_csv(csv, index=False)
            st.download_button("⬇️ Download First Table as CSV", csv.getvalue(), file_name="company_data.csv", mime="text/csv")

        if any(all_metrics.values()):
            pdf_path = download_pdf(all_metrics)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download Metrics PDF", f, file_name="company_summary.pdf", mime="application/pdf")

        if not all_tables and not any(all_metrics.values()):
            st.warning("No usable financial data found.")
