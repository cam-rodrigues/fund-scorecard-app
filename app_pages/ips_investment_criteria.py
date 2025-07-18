import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
from datetime import datetime

# --- Step 2: Extract Time Period ---
def extract_time_period(text):
    match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', text)
    return match.group(0) if match else "Unknown"

# --- Step 4: TOC Page Number Matcher (robust to spacing OR dots) ---
def find_section_page(text, section_title):
    pattern = rf"{re.escape(section_title)}[\s\.]*?(\d+)"
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None

# --- Step 5: Extract Metrics from Fund Scorecard ---
def extract_fund_scorecard_blocks(pdf, scorecard_start):
    blocks = []
    current_fund = None
    for page in pdf.pages[scorecard_start - 1:]:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if re.match(r'^[A-Z][A-Za-z0-9 ,\-()]+$', line.strip()) and "Fund Meets" not in line:
                current_fund = {
                    "name": line.strip(),
                    "metrics": []
                }
                blocks.append(current_fund)
            elif current_fund and ("Pass" in line or "Review" in line):
                metric_match = re.match(r"(.+?)\s+(Pass|Review)$", line.strip())
                if metric_match:
                    metric_name, status = metric_match.groups()
                    current_fund["metrics"].append((metric_name.strip(), status))
    return blocks

# --- Step 5.5: Apply IPS Status Rules ---
def apply_ips_scoring(fund):
    metrics = fund["metrics"][:11]  # Only first 11 IPS metrics
    fails = sum(1 for m in metrics if m[1] == "Review")
    if fails <= 4:
        status = "Passed IPS Screen"
    elif fails == 5:
        status = "Informal Watch (IW)"
    else:
        status = "Formal Watch (FW)"
    return [("Fail" if m[1] == "Review" else "Pass") for m in metrics], status

# --- Step 6: Extract Ticker + Category from Performance Section ---
def build_perf_lookup(pdf, perf_page):
    lookup = {}
    text = pdf.pages[perf_page - 1].extract_text()
    lines = text.split("\n") if text else []
    current_category = None
    for i, line in enumerate(lines):
        if line.strip() and not re.search(r"[A-Z]{4,6}X?", line):
            current_category = line.strip()
        if i + 1 < len(lines):
            fund = lines[i].strip()
            maybe_ticker = lines[i + 1].strip()
            if re.fullmatch(r"[A-Z]{4,6}X?", maybe_ticker):
                lookup[fund] = {
                    "ticker": maybe_ticker,
                    "category": current_category
                }
    return lookup

# --- Step 7: Build Output Table ---
def build_final_df(blocks, perf_lookup, time_period):
    rows = []
    for fund in blocks:
        name = fund["name"]
        metrics, ips_status = apply_ips_scoring(fund)
        match = perf_lookup.get(name, {})
        row = [
            name,
            match.get("category", "Unknown"),
            match.get("ticker", "Unknown"),
            time_period,
            "$"
        ] + metrics + [ips_status]
        rows.append(row)
    columns = ["Investment Option", "Category", "Ticker", "Time Period", "Plan Assets"] + [str(i) for i in range(1, 12)] + ["IPS Status"]
    return pd.DataFrame(rows, columns=columns)

# --- Streamlit UI ---
def run():
    st.set_page_config(page_title="IPS Investment Criteria Evaluator", layout="wide")
    st.title("IPS Investment Criteria Evaluator")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="ips_pdf_upload")
    if not uploaded_file:
        return

    with pdfplumber.open(uploaded_file) as pdf:
        # Step 2 – Time Period
        page1 = pdf.pages[0].extract_text()
        time_period = extract_time_period(page1 or "")
        st.info(f"Time Period Detected: **{time_period}**")

        # Step 4 – TOC and Page Number Detection
        toc = pdf.pages[1].extract_text()
        st.text("TOC (Page 2):\n" + toc)  # Optional: for debugging future uploads

        perf_page = find_section_page(toc, "Fund Performance: Current vs. Proposed Comparison")
        scorecard_page = find_section_page(toc, "Fund Scorecard")

        if not perf_page or not scorecard_page:
            st.error("Could not detect required sections from Table of Contents.")
            return

        # Step 5 – Extract IPS Metrics
        blocks = extract_fund_scorecard_blocks(pdf, scorecard_page)

        # Step 6 – Lookup for Ticker + Category
        perf_lookup = build_perf_lookup(pdf, perf_page)

        # Step 7 – Build Final Data Table
        df = build_final_df(blocks, perf_lookup, time_period)
        st.dataframe(df)

        # Step 8 – Export Options
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="IPS_Results.csv", mime="text/csv")

        excel_io = BytesIO()
        with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="IPS Results")
        st.download_button("Download Excel", data=excel_io.getvalue(), file_name="IPS_Results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

