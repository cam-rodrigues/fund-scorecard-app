import re
import pdfplumber
import pandas as pd
import numpy as np
import streamlit as st
from calendar import month_name

# === Utility ===
def extract_report_date(text):
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {year}"
        return f"As of {month_name[m]} {d}, {year}"
    return "Unknown"

def extract_number(s):
    m = re.search(r"([-+]?\d*\.?\d+)", s or "")
    return float(m.group(1)) if m else np.nan

def extract_percent(s):
    m = re.search(r"([-+]?\d*\.?\d+)%", s or "")
    return float(m.group(1)) if m else np.nan

def extract_rank(s):
    m = re.search(r"(\d+)", s or "")
    return int(m.group(1)) if m else np.nan

def is_passive(name):
    return "index" in name.lower()

def pass_fail(val, metric_name, passive):
    if pd.isna(val):
        return False
    if metric_name == "Manager Tenure":
        return val >= 3
    if metric_name.startswith("Excess Performance"):
        return val > 0
    if "Peer Return Rank" in metric_name or "Sharpe Ratio Rank" in metric_name or "Sortino Ratio Rank" in metric_name:
        return val <= 50
    if metric_name == "Expense Ratio Rank":
        return val <= 50
    if "R-Squared" in metric_name:
        return val >= 95 if passive else True
    if "Tracking Error Rank" in metric_name:
        return val < 90 if passive else True
    return False

# === Step 1 ===
def process_page1(page_text):
    date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", page_text)
    quarter = extract_report_date(date_match.group(0)) if date_match else "Unknown"
    prepared_for = ""
    prepared_by = ""
    pf = re.search(r"Prepared For[:\s]*(.+)", page_text)
    pb = re.search(r"Prepared By[:\s]*(.+)", page_text)
    if pf:
        prepared_for = pf.group(1).strip()
    if pb:
        prepared_by = pb.group(1).strip()
    st.session_state["report_metadata"] = {
        "Quarter": quarter,
        "Prepared For": prepared_for or "N/A",
        "Prepared By": prepared_by or "N/A"
    }

# === Step 2 ===
def process_toc(full_text):
    def find_page(pattern):
        m = re.search(rf"{pattern}.*?(\d{{1,3}})", full_text, flags=re.IGNORECASE)
        return int(m.group(1)) - 1 if m else None
    toc = {}
    toc["Fund Scorecard"] = find_page("Fund Scorecard")
    toc["Fund Performance"] = find_page("Fund Performance")
    toc["Calendar Year Performance"] = find_page("Calendar Year Performance")
    toc["MPT 3Yr Risk Analysis"] = find_page("MPT Statistics.*?3Yr")
    toc["MPT 5Yr Risk Analysis"] = find_page("MPT Statistics.*?5Yr")
    toc["Fund Factsheets"] = find_page("Fund Factsheet") or find_page("Factsheet")
    st.session_state["toc_pages"] = toc

# === Step 3 ===
def step3_process_scorecard(pdf):
    start_page = st.session_state.get("toc_pages", {}).get("Fund Scorecard")
    if start_page is None or start_page >= len(pdf.pages):
        st.error("Scorecard page not found.")
        return []
    raw = pdf.pages[start_page].extract_text() or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    fund_blocks = []
    current = None
    for line in lines:
        if ("Fund" in line and len(line.split()) <= 6) or line.isupper():
            if current:
                fund_blocks.append(current)
            current = {"Fund Name": line, "Metrics": []}
        elif current:
            if ":" in line:
                metric, info = line.split(":", 1)
                current["Metrics"].append({"Metric": metric.strip(), "Info": info.strip()})
            else:
                current["Metrics"].append({"Metric": "Unknown", "Info": line})
    if current:
        fund_blocks.append(current)
    st.session_state["fund_blocks"] = fund_blocks

# === Step 5 ===
def step5_process_performance(pdf):
    start_page = st.session_state.get("toc_pages", {}).get("Fund Performance")
    if start_page is None or start_page >= len(pdf.pages):
        st.error("Fund Performance page not found.")
        return {}
    text = pdf.pages[start_page].extract_text() or ""
    fund_blocks = st.session_state.get("fund_blocks", [])
    name_to_ticker = {}
    for block in fund_blocks:
        name = block["Fund Name"]
        pattern = rf"{re.escape(name)}.*?\((\w{{1,5}})\)"
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            name_to_ticker[name] = m.group(1).upper()
        else:
            name_to_ticker[name] = "UNKNOWN"
    st.session_state["fund_tickers"] = name_to_ticker

# === Step 6 ===
def step6_process_factsheets(pdf):
    factsheet_page = st.session_state.get("toc_pages", {}).get("Fund Factsheets")
    if factsheet_page is None or factsheet_page >= len(pdf.pages):
        st.error("Factsheet page not found.")
        return []
    raw = pdf.pages[factsheet_page].extract_text() or ""
    fund_blocks = st.session_state.get("fund_blocks", [])
    facts = []
    for block in fund_blocks:
        facts.append({
            "Fund Name": block["Fund Name"],
            "Benchmark": "N/A",
            "Category": "N/A",
            "Net Assets": "N/A",
            "Manager": "N/A",
            "Avg Market Cap": "N/A",
            "Expense Ratio": "N/A"
        })
    st.session_state["fund_factsheets"] = facts

# === Scorecard / IPS Table Builder ===
def build_scorecard_tables(fund_blocks, tickers_map):
    scorecard_rows = []
    ips_summary = []

    for block in fund_blocks:
        name = block["Fund Name"]
        ticker = tickers_map.get(name, "UNKNOWN")
        metrics = {m["Metric"]: m["Info"] for m in block["Metrics"]}
        passive = is_passive(name)

        row_vals = {
            "Investment Option": name,
            "Ticker": ticker,
            "Manager Tenure": extract_number(metrics.get("Manager Tenure", "")),
            "Excess Performance (3Yr)": extract_percent(metrics.get("Excess Performance (3Yr)", "")),
            "Excess Performance (5Yr)": extract_percent(metrics.get("Excess Performance (5Yr)", "")),
            "Peer Return Rank (3Yr)": extract_rank(metrics.get("Peer Return Rank (3Yr)", "")),
            "Peer Return Rank (5Yr)": extract_rank(metrics.get("Peer Return Rank (5Yr)", "")),
            "Expense Ratio Rank": extract_rank(metrics.get("Expense Ratio Rank", "")),
            "Sharpe Ratio Rank (3Yr)": extract_rank(metrics.get("Sharpe Ratio Rank (3Yr)", "")),
            "Sharpe Ratio Rank (5Yr)": extract_rank(metrics.get("Sharpe Ratio Rank (5Yr)", "")),
            "R-Squared (3Yr)": extract_percent(metrics.get("R-Squared (3Yr)", "")),
            "R-Squared (5Yr)": extract_percent(metrics.get("R-Squared (5Yr)", "")),
            "Sortino Ratio Rank (3Yr)": extract_rank(metrics.get("Sortino Ratio Rank (3Yr)", "")),
            "Sortino Ratio Rank (5Yr)": extract_rank(metrics.get("Sortino Ratio Rank (5Yr)", "")),
            "Tracking Error Rank (3Yr)": extract_rank(metrics.get("Tracking Error Rank (3Yr)", "")),
            "Tracking Error Rank (5Yr)": extract_rank(metrics.get("Tracking Error Rank (5Yr)", "")),
        }

        display_row = {
            "Investment Option": name,
            "Ticker": ticker,
        }
        metric_columns = [
            "Manager Tenure",
            "Excess Performance (3Yr)",
            "Excess Performance (5Yr)",
            "Peer Return Rank (3Yr)",
            "Peer Return Rank (5Yr)",
            "Expense Ratio Rank",
            "Sharpe Ratio Rank (3Yr)",
            "Sharpe Ratio Rank (5Yr)",
            "R-Squared (3Yr)",
            "R-Squared (5Yr)",
            "Sortino Ratio Rank (3Yr)",
            "Sortino Ratio Rank (5Yr)",
            "Tracking Error Rank (3Yr)",
            "Tracking Error Rank (5Yr)",
        ]
        fail_count = 0
        for col in metric_columns:
            val = row_vals[col]
            passed = pass_fail(val, col, passive)
            display_row[col] = "✅" if passed else "❌"
            if not passed:
                fail_count += 1

        if fail_count <= 4:
            overall = "Passed IPS Screen"
        elif fail_count == 5:
            overall = "Informal Watch (IW)"
        else:
            overall = "Formal Watch (FW)"

        scorecard_rows.append(display_row)
        ips_summary.append({
            "Investment Option": name,
            "Ticker": ticker,
            "Fail Count": fail_count,
            "Overall IPS Status": overall,
        })

    df_scorecard = pd.DataFrame(scorecard_rows)
    df_ips = pd.DataFrame(ips_summary)
    return df_scorecard, df_ips

# === Entry point expected by your loader ===
def run():
    st.title("MPI Scorecard & IPS Metrics")
    uploaded = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if not uploaded:
        st.warning("Please upload an MPI PDF to continue.")
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1
        first_text = pdf.pages[0].extract_text() or ""
        process_page1(first_text)

        # Step 2 (try page 1 and 2 combined for TOC)
        toc_text = ""
        if len(pdf.pages) > 1:
            toc_text += (pdf.pages[1].extract_text() or "")
        process_toc(toc_text)

        # Step 3
        step3_process_scorecard(pdf)

        # Step 5
        step5_process_performance(pdf)

        # Step 6
        step6_process_factsheets(pdf)

    fund_blocks = st.session_state.get("fund_blocks", [])
    fund_tickers = st.session_state.get("fund_tickers", {})

    if not fund_blocks:
        st.error("No fund scorecard blocks extracted.")
        return

    st.subheader("Scorecard Metrics")  # Table 1
    df_scorecard, df_ips = build_scorecard_tables(fund_blocks, fund_tickers)
    st.dataframe(df_scorecard, use_container_width=True)

    st.subheader("IPS Summary")  # Table 2
    st.dataframe(df_ips, use_container_width=True)
