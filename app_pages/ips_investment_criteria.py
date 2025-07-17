import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
from difflib import get_close_matches

IPS_METRICS = [
    "Manager Tenure", "R-Squared (3Yr)", "Return Rank (3Yr)", "Sharpe Ratio Rank (3Yr)",
    "Sortino Ratio Rank (3Yr)", "R-Squared (5Yr)", "Return Rank (5Yr)", "Sharpe Ratio Rank (5Yr)",
    "Sortino Ratio Rank (5Yr)", "Expense Ratio Rank", "Style Match"
]

COLUMN_HEADERS = [
    "Name Of Fund", "Category", "Ticker", "Time Period", "Plan Assets"
] + [str(i+1) for i in range(11)] + ["IPS Status"]

# --- Step 1: Extract funds from all pages, not just the labeled section
def extract_all_performance_funds(pdf):
    funds = []
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        current_category = None
        for i in range(len(lines) - 1):
            line = lines[i].strip()
            next_line = lines[i+1].strip()

            if re.search(r"(Cap|Growth|Value|Income|Fixed|International|Blend)", line, re.IGNORECASE):
                current_category = line

            match = re.match(r"(.+?)\s+([A-Z]{4,6}X?)$", line)
            if match:
                name = match.group(1).strip()
                ticker = match.group(2).strip()
                funds.append({
                    "name": name,
                    "ticker": ticker,
                    "category": current_category or "Unknown"
                })
    return funds

# --- Step 2: Extract Pass/Review metrics from scorecard pages
def extract_scorecard_metrics(pdf):
    scorecard = {}
    fund_name = None
    metrics = []

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if re.match(r".+\s+[A-Z]{4,6}X?$", line):
                if fund_name and metrics:
                    scorecard[fund_name] = metrics
                parts = line.rsplit(" ", 1)
                fund_name = parts[0].strip()
                metrics = []
            elif "Pass" in line or "Review" in line:
                result = "Pass" if "Pass" in line else "Review"
                metrics.append(result)
                if len(metrics) == 11:
                    scorecard[fund_name] = metrics
                    fund_name, metrics = None, []
    return scorecard

# --- Step 3: Status Logic
def determine_status(metrics):
    metrics = metrics[:10] + ["Pass"]
    fail_count = metrics.count("Review")
    if fail_count <= 4:
        return "Passed IPS Screen"
    elif fail_count == 5:
        return "Informal Watch (IW)"
    else:
        return "Formal Watch (FW)"

# --- Step 4: Final Table Builder
def build_ips_table(performance_funds, scorecard_metrics):
    quarter = f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year}"
    data = []

    for perf in performance_funds:
        name = perf["name"]
        match = get_close_matches(name, scorecard_metrics.keys(), n=1, cutoff=0.8)
        if not match:
            continue
        matched_name = match[0]
        metrics = scorecard_metrics[matched_name]
        metrics = metrics[:10] + ["Pass"]
        status = determine_status(metrics)
        row = [name, perf["category"], perf["ticker"], quarter, "$"] + metrics + [status]
        data.append(row)

    return pd.DataFrame(data, columns=COLUMN_HEADERS)

# --- Streamlit App UI
def run():
    st.set_page_config(page_title="IPS Investment Criteria", layout="wide")
    st.title("IPS Investment Criteria Table Generator")
    st.markdown("Upload an MPI PDF and generate a table evaluating funds against 11 IPS metrics.")

    uploaded_file = st.file_uploader("Upload MPI.pdf", type=["pdf"])

    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            perf_funds = extract_all_performance_funds(pdf)
            scorecard = extract_scorecard_metrics(pdf)
            df = build_ips_table(perf_funds, scorecard)

            st.success(f"Extracted {len(df)} fund(s).")
            st.dataframe(df, use_container_width=True)

            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                "Download Excel File",
                data=buffer,
                file_name="ips_investment_criteria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    run()
