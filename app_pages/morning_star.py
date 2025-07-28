import re
import streamlit as st
import pdfplumber
from calendar import month_name

# Utility: Extract report date from Morningstar cover page
def extract_report_date_ms(text):
    # Morningstar often prints date like "As of MM/DD/YYYY"
    m = re.search(r"As of (\d{1,2}/\d{1,2}/20\d{2})", text)
    if m:
        return m.group(1)
    # Fallback: any mm/dd/yyyy
    m = re.search(r"(\d{1,2}/\d{1,2}/20\d{2})", text)
    return m.group(1) if m else None

# Step 1: Cover Page Extraction
def process_cover_page_ms(text):
    """Extracts cover page metadata: report date, fund name, ticker."""
    out = {}
    out['report_date'] = extract_report_date_ms(text)
    # Fund name and ticker line
    m = re.search(r"Morningstar\s+Fund\s+Report\s*-\s*(.*?)\s+\(([^)]+)\)", text)
    if m:
        out['fund_name'] = m.group(1).strip()
        out['ticker'] = m.group(2).strip()
    else:
        out['fund_name'] = None
        out['ticker'] = None
    return out

# Step 2: Table of Contents
def process_toc_ms(text):
    """Identifies page numbers for key sections from Morningstar TOC."""
    pages = {}
    patterns = {
        'summary_page': r"Summary\s+(\d+)",
        'performance_page': r"Performance\s+(\d+)",
        'holdings_page': r"Holdings\s+(\d+)",
        'risk_page': r"Risk\s+(\d+)",
        'fees_page': r"Fees & Expenses\s+(\d+)"
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        pages[key] = int(m.group(1)) if m else None
    return pages

# Step 3: Summary Section
def step3_summary_ms(pdf, page):
    st.subheader("Morningstar: Summary")
    if not page:
        st.error("Summary page not found.")
        return
    txt = pdf.pages[page-1].extract_text() or ""
    # Display key bullet points
    for line in txt.splitlines():
        if line.strip():
            st.write(f"- {line.strip()}")

# Step 4: Performance Section
def step4_performance_ms(pdf, page):
    st.subheader("Morningstar: Performance")
    if not page:
        st.error("Performance page not found.")
        return
    # Assuming table: columns Year-to-Date, 1yr, 3yr, 5yr, 10yr
    lines = pdf.pages[page-1].extract_text().splitlines()
    header = []
    data = []
    for ln in lines:
        parts = ln.split()
        if 'YTD' in ln:
            header = parts
        elif header and re.match(r"\d|\(|-", parts[0]):
            data.append(parts)
    if header and data:
        import pandas as pd
        df = pd.DataFrame(data, columns=header)
        st.dataframe(df)
        st.session_state['ms_performance'] = df
    else:
        st.warning("Could not parse performance table.")

# Step 5: Holdings Section
def step5_holdings_ms(pdf, page):
    st.subheader("Morningstar: Holdings")
    if not page:
        st.error("Holdings page not found.")
        return
    # Simplest: display first 10 holdings
    lines = pdf.pages[page-1].extract_text().splitlines()
    for ln in lines[:10]:
        st.write(f"- {ln}")

# Main app for Morningstar parser
def run_morningstar():
    st.title("Morningstar Report Parser")
    uploaded = st.file_uploader("Upload Morningstar PDF", type="pdf")
    if not uploaded:
        return
    with pdfplumber.open(uploaded) as pdf:
        # Cover Page
        with st.expander("Step 1: Cover Page", expanded=True):
            text0 = pdf.pages[0].extract_text() or ""
            meta = process_cover_page_ms(text0)
            st.write(meta)
            st.session_state['ms_meta'] = meta
        # TOC
        with st.expander("Step 2: Table of Contents", expanded=False):
            toc_text = "".join(p.extract_text() or "" for p in pdf.pages[:5])
            toc = process_toc_ms(toc_text)
            st.write(toc)
            st.session_state['ms_toc'] = toc
        # Summary
        with st.expander("Step 3: Summary", expanded=False):
            step3_summary_ms(pdf, st.session_state['ms_toc'].get('summary_page'))
        # Performance
        with st.expander("Step 4: Performance", expanded=False):
            step4_performance_ms(pdf, st.session_state['ms_toc'].get('performance_page'))
        # Holdings
        with st.expander("Step 5: Holdings", expanded=False):
            step5_holdings_ms(pdf, st.session_state['ms_toc'].get('holdings_page'))

if __name__ == "__main__":
    run_morningstar()
