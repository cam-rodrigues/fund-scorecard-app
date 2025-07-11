import streamlit as st
import pdfplumber
import re
from collections import defaultdict

# === Patterns for matching ===
METRIC_TERMS = [
    "Sharpe Ratio", "Information Ratio", "Sortino Ratio", "Treynor Ratio",
    "Standard Deviation", "Tracking Error", "Alpha", "Beta", "R²", "Upside Capture",
    "Downside Capture", "Expense Ratio", "Manager Tenure", "Net Assets",
    "Turnover Ratio", "Benchmark", "Category"
]

FUND_HEADER_PATTERNS = [
    r"Manager Name[:\s]", r"Benchmark[:\s]", r"Category[:\s]",
    r"(?i)^([A-Za-z].+?)\s+[A-Z]{4,6}X\b",  # Fund Name + Ticker
    r"\bExpense Ratio\b", r"\b03/3[01]/\d{4}\b"
]

def detect_terms(text):
    matches = []
    for term in METRIC_TERMS:
        if term.lower() in text.lower():
            matches.append(term)
    return matches

def detect_fund_header(text):
    return any(re.search(pattern, text) for pattern in FUND_HEADER_PATTERNS)

def main():
    st.title("🔍 PDF Financial Term & Fund Navigator")
    st.markdown("Upload an MPI-style PDF. This tool finds financial terms and fund sections using fast pattern detection — no AI required.")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="fast_navigator_pdf")

    if uploaded_pdf:
        with pdfplumber.open(uploaded_pdf) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]

        term_to_pages = defaultdict(list)
        fund_pages = {}

        with st.spinner("Scanning PDF..."):
            for i, text in enumerate(pages):
                clean_text = text.replace("\n", " ").strip()

                # Find known metrics
                terms_found = detect_terms(clean_text)
                for term in terms_found:
                    term_to_pages[term].append(i)

                # Find fund pages
                if detect_fund_header(clean_text) and i > 20:
                    first_line = clean_text.splitlines()[0].strip()
                    if len(first_line.split()) > 2:
                        fund_pages[first_line] = i

        st.markdown("## Select by Financial Term")
        if term_to_pages:
            term = st.selectbox("Choose a financial metric:", sorted(term_to_pages))
            for pg in term_to_pages[term]:
                st.markdown(f"### Page {pg + 1}")
                st.text_area(f"Match for '{term}'", pages[pg], height=400)
        else:
            st.info("No standard financial metrics found.")

        st.markdown("---")
        st.markdown("## Select by Fund Page")
        if fund_pages:
            fund = st.selectbox("Choose a fund section:", sorted(fund_pages))
            pg = fund_pages[fund]
            st.markdown(f"### Fund Page {pg + 1}")
            st.text_area(f"Fund: {fund}", pages[pg], height=400)
        else:
            st.info("No fund section pages detected.")

def run():
    main()
