import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

# -------------------------
# STEP 2 – Extract Time Period (from Page 1)
# -------------------------
def extract_time_period(text):
    match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', text)
    return match.group(0) if match else "Unknown"

# -------------------------
# STEP 3 – Extract Info from Page 1
# -------------------------
def extract_page1_info(text):
    total_options = re.search(r"Total Options:\s*(\d+)", text)
    prepared_for = re.search(r"Prepared For:\s*(.+)", text)
    prepared_by = re.search(r"Prepared By:\s*(.+)", text)
    return {
        "Total Options": total_options.group(1) if total_options else "Unknown",
        "Prepared For": prepared_for.group(1).strip() if prepared_for else "Unknown",
        "Prepared By": prepared_by.group(1).strip() if prepared_by else "Unknown"
    }

# -------------------------
# STEP 4 – Extract Section Page Numbers from TOC
# -------------------------
def find_section_page(text, section_title):
    pattern = rf"{re.escape(section_title)}[\s\.]*?(\d+)"
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None

# -------------------------
# STEP 5 – Extract Funds + Metrics from Scorecard
# -------------------------
def extract_scorecard_blocks(pdf, scorecard_start):
    blocks = []
    current_fund = None
    for page in pdf.pages[scorecard_start - 1:]:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if "Fund Meets" in line or "Watchlist" in line:
                continue
            if re.match(r'^[A-Z].{5,}$', line):
                current_fund = {"name": line, "metrics": []}
                blocks.append(current_fund)
            elif current_fund and ("Pass" in line or "Review" in line):
                m = re.match(r"(.+?)\s+(Pass|Review)$", line)
                if m:
                    current_fund["metrics"].append((m.group(1).strip(), m.group(2)))
    return blocks

# -------------------------
# STEP 6 – Apply IPS Logic
# -------------------------
def apply_ips_scoring(fund):
    raw_metrics = fund["metrics"][:11]
    while len(raw_metrics) < 11:
        raw_metrics.append(("Missing", "Review"))
    status_list = []
    fail_count = 0
    for _, status in raw_metrics:
        passfail = "Fail" if status == "Review" else "Pass"
        status_list.append(passfail)
        if passfail == "Fail":
            fail_count += 1
    if fail_count <= 4:
        status = "Passed IPS Screen"
    elif fail_count == 5:
        status = "Informal Watch (IW)"
    else:
        status = "Formal Watch (FW)"
    return status_list, status

# -------------------------
# STEP 7 – Extract Fund Ticker and Category
# -------------------------
def build_perf_lookup(pdf, perf_page):
    lookup = {}
    text = pdf.pages[perf_page - 1].extract_text()
    lines = text.split("\n") if text else []
    current_category = None
    for i in range(len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if re.fullmatch(r"[A-Z]{4,6}X?", next_line):
                fund_name = line
                ticker = next_line
                lookup[fund_name] = {
                    "ticker": ticker,
                    "category": current_category or "Unknown"
                }
        if "Category" in line:
            current_category = line.replace("Category", "").strip()
    return lookup

# -------------------------
# STEP 8 – Build Final Output Table (17+3 Columns)
# -------------------------
def build_final_df(blocks, perf_lookup, time_period, page1_info):
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
        ] + metrics + [ips_status] + [
            page1_info["Prepared For"],
            page1_info["Prepared By"],
            page1_info["Total Options"]
        ]
        rows.append(row)

    columns = ["Investment Option", "Category", "Ticker", "Time Period", "Plan Assets"] + [str(i) for i in range(1, 12)] + ["IPS Status", "Prepared For", "Prepared By", "Total Options"]
    return pd.DataFrame(rows, columns=columns)

# -------------------------
# STEP 1 + 9 – Streamlit UI
# -------------------------
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

        # Step 3 – Other Page 1 Info
        page1_info = extract_page1_info(page1 or "")

        # Step 4 – TOC Page Numbers
        toc = pdf.pages[1].extract_text()
        perf_page = find_section_page(toc, "Fund Performance: Current vs. Proposed Comparison")
        scorecard_page = find_section_page(toc, "Fund Scorecard")
        if not perf_page or not scorecard_page:
            st.error("❌ Could not find required section page numbers.")
            return

        # Step 5 – Extract Scorecard Blocks
        scorecard_blocks = extract_scorecard_blocks(pdf, scorecard_page)

        # Step 7 – Performance Ticker/Category
        perf_lookup = build_perf_lookup(pdf, perf_page)

        # Step 8 – Final Table
        df = build_final_df(scorecard_blocks, perf_lookup, time_period, page1_info)
        st.dataframe(df)

        # Step 9 – Downloads
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="IPS_Results.csv", mime="text/csv")

        excel_io = BytesIO()
        with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="IPS Results")
        st.download_button("Download Excel", data=excel_io.getvalue(), file_name="IPS_Results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
