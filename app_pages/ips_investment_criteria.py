import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
from difflib import get_close_matches

# --- IPS Metric Labels (exact order) ---
IPS_METRICS = [
    "Manager Tenure",
    "R-Squared (3Yr)",
    "Return Rank (3Yr)",
    "Sharpe Ratio Rank (3Yr)",
    "Sortino Ratio Rank (3Yr)",  # Alt: Tracking Error (3Yr)
    "R-Squared (5Yr)",
    "Return Rank (5Yr)",
    "Sharpe Ratio Rank (5Yr)",
    "Sortino Ratio Rank (5Yr)",  # Alt: Tracking Error (5Yr)
    "Expense Ratio Rank",
    "Style Match",  # Always Pass
]

COLUMN_HEADERS = [
    "Name Of Fund", "Category", "Ticker", "Time Period", "Plan Assets"
] + [str(i+1) for i in range(11)] + ["IPS Status"]

# --- Step 1: Extract Performance Funds (Name, Ticker, Category) ---
def extract_performance_funds(pdf):
    funds = []
    for page in pdf.pages:
        if "Fund Performance: Current vs. Proposed Comparison" not in (page.extract_text() or ""):
            continue
        lines = page.extract_text().split("\n")
        current_category = None

        for i in range(len(lines) - 1):
            line = lines[i].strip()
            next_line = lines[i+1].strip()

            # Detect category (e.g., Mid Cap Growth)
            if re.search(r"(Cap|Growth|Value|Income|Fixed|International)", line, re.IGNORECASE):
                current_category = line

            # Detect fund name + ticker
            match = re.match(r"(.+?)\s+([A-Z]{4,6}X?)$", line)
            if match:
                fund_name = match.group(1).strip()
                ticker = match.group(2).strip()
                funds.append({
                    "name": fund_name,
                    "category": current_category or "Unknown",
                    "ticker": ticker
                })
    return funds

# --- Step 2: Extract Scorecard Metrics (Pass/Review per Fund) ---
def extract_scorecard_metrics(pdf):
    scorecard = {}
    fund_name = None
    metrics = []

    for page in pdf.pages:
        if "Fund Scorecard" not in (page.extract_text() or ""):
            continue

        lines = page.extract_text().split("\n")
        for line in lines:
            line = line.strip()
            # Detect new fund block
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

# --- Step 3: Determine IPS Status ---
def determine_status(metrics):
    metrics = metrics[:10] + ["Pass"]  # Always pass #11
    fail_count = metrics.count("Review")
    if fail_count <= 4:
        return "Passed IPS Screen"
    elif fail_count == 5:
        return "Informal Watch (IW)"
    else:
        return "Formal Watch (FW)"

# --- Step 4: Combine + Build Final Table ---
def build_ips_table(performance_funds, scorecard_metrics):
    quarter = datetime.today().strftime("Q{} %Y".format((datetime.today().month - 1)//3 + 1))
    data = []

    for perf in performance_funds:
        name = perf["name"]
        match = get_close_matches(name, scorecard_metrics.keys(), n=1, cutoff=0.8)
        if not match:
            continue
        matched_name = match[0]
        metrics = scorecard_metrics[matched_name]
        metrics = metrics[:10] + ["Pass"]  # Force #11 to Pass
        status = determine_status(metrics)
        row = [name, perf["category"], perf["ticker"], quarter, "$"] + metrics + [status]
        data.append(row)

    return pd.DataFrame(data, columns=COLUMN_HEADERS)

# --- Streamlit App ---
def run():
    st.title("IPS Investment Criteria Table Generator")
    st.markdown("Upload an MPI PDF and generate a table with IPS evaluation per fund.")

    uploaded_file = st.file_uploader("Upload MPI.pdf", type=["pdf"])

    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            perf_funds = extract_performance_funds(pdf)
            scorecard = extract_scorecard_metrics(pdf)
            df = build_ips_table(perf_funds, scorecard)

            st.dataframe(df, use_container_width=True)

            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button(
                "Download as Excel",
                buffer.getvalue(),
                "ips_investment_criteria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    run()
