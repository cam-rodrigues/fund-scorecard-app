# page_module.py

import re
import streamlit as st
import pdfplumber
import pandas as pd
from calendar import month_name

# ─── Utility Functions ─────────────────────────────────────────────────────────────

def extract_report_date(text: str) -> str | None:
    """Find first quarter‑end or mm/dd/yyyy and format human‑readable."""
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for m_str, d_str, y in dates:
        m, d = int(m_str), int(d_str)
        if (m, d) in [(3,31),(6,30),(9,30),(12,31)]:
            q = { (3,31):"1st",(6,30):"2nd",(9,30):"3rd",(12,31):"4th"}[(m,d)]
            return f"{q} QTR, {y}"
        return f"As of {month_name[m]} {d}, {y}"
    return None

# ─── Step Functions ────────────────────────────────────────────────────────────────

def process_overview(pdf):
    """Extract fund name, ticker, strategy, date, etc."""
    txt = pdf.pages[0].extract_text() or ""
    st.subheader("Overview / Page 1")
    name = re.search(r"Morningstar Fund Report:\s*(.+)", txt)
    if name:
        st.write(f"- **Fund Name:** {name.group(1).strip()}")
    rd = extract_report_date(txt)
    if rd:
        st.write(f"- **Report Date:** {rd}")
    # …and any other top‐of‐page fields you need…

def process_performance(pdf):
    """Extract performance table (YTD, 1Yr, 3Yr, 5Yr, 10Yr, etc.)."""
    st.subheader("Performance Summary")
    # Locate the page or pages that contain the performance table
    perf_lines = []
    for p in pdf.pages:
        text = p.extract_text() or ""
        if "Performance as of" in text:
            perf_lines += text.splitlines()
    # Parse perf_lines into a DataFrame
    # TODO: adapt regex to your Morningstar layout
    data = []
    for ln in perf_lines:
        m = re.match(r"^(?P<label>[^ ]+)\s+(?P<ytd>-?\d+\.\d+)%\s+(?P<one>-?\d+\.\d+)%\s+(?P<three>-?\d+\.\d+)%\s+(?P<five>-?\d+\.\d+)%\s+(?P<ten>-?\d+\.\d+)%", ln)
        if m:
            data.append(m.groupdict())
    if data:
        df = pd.DataFrame(data).set_index("label")
        st.dataframe(df, use_container_width=True)
    else:
        st.write("_Could not parse performance table_")

def process_holdings(pdf):
    """Extract top‐holdings table."""
    st.subheader("Top Holdings")
    # TODO: find page(s) with 'Top 10 Holdings' and parse into a DataFrame
    # e.g. look for lines starting with rank numbers 1–10, extract name + weight
    st.write("_Holdings parsing not yet implemented._")

def process_risk_metrics(pdf):
    """Extract risk measures (Sharpe, Sortino, Beta, etc.)."""
    st.subheader("Risk Metrics")
    # TODO: locate 'Risk Statistics' section and parse metrics
    st.write("_Risk‑metric parsing not yet implemented._")

# ─── Main App Entry Point ─────────────────────────────────────────────────────────

def run():
    st.title("Morningstar Report Reader")
    uploaded = st.file_uploader("Upload Morningstar PDF", type="pdf")
    if not uploaded:
        st.info("Please upload a Morningstar PDF report to get started.")
        return

    with pdfplumber.open(uploaded) as pdf:
        with st.expander("Step 1: Overview / Page 1", expanded=True):
            process_overview(pdf)

        with st.expander("Step 2: Performance Summary", expanded=False):
            process_performance(pdf)

        with st.expander("Step 3: Top Holdings", expanded=False):
            process_holdings(pdf)

        with st.expander("Step 4: Risk Metrics", expanded=False):
            process_risk_metrics(pdf)

        # …add more expanders/steps as needed…

if __name__ == "__main__":
    run()
