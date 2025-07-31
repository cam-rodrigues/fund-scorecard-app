import re
import pdfplumber
from calendar import month_name
import pandas as pd
from rapidfuzz import fuzz
import streamlit as st

# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {year}"
        return f"As of {month_name[m]} {d}, {year}"
    return "Unknown"

# === Step 1: Header / Report Metadata ===
def process_page1(page_text):
    # Quarter/Year
    date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", page_text)
    quarter = "Unknown"
    if date_match:
        quarter = extract_report_date(date_match.group(0))
    # Prepared for / by (fallback if missing)
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
    st.markdown("**Step 1: Report Header / Metadata**")
    st.write(st.session_state["report_metadata"])
    return st.session_state["report_metadata"]

# === Step 2: Table of Contents / Section Locator ===
def process_toc(full_text):
    # naive regex-based finders; adjust pattern complexity if needed
    def find_page(pattern):
        m = re.search(rf"{pattern}.*?(\d{{1,3}})", full_text, flags=re.IGNORECASE)
        return int(m.group(1)) - 1 if m else None  # convert to 0-index

    toc = {}
    toc["Fund Scorecard"] = find_page("Fund Scorecard")
    toc["Fund Performance"] = find_page("Fund Performance")
    toc["Calendar Year Performance"] = find_page("Calendar Year Performance")
    toc["MPT 3Yr Risk Analysis"] = find_page("MPT Statistics.*?3Yr")
    toc["MPT 5Yr Risk Analysis"] = find_page("MPT Statistics.*?5Yr")
    toc["Fund Factsheets"] = find_page("Fund Factsheet") or find_page("Factsheet")

    st.session_state["toc_pages"] = toc
    st.markdown("**Step 2: Table of Contents / Section Pages**")
    st.write(toc)
    return toc

# === Step 3: Scorecard Metrics Extraction ===
def step3_process_scorecard(pdf):
    start_page = st.session_state.get("toc_pages", {}).get("Fund Scorecard")
    if start_page is None:
        st.error("Scorecard start page not found in TOC.")
        return []

    raw = pdf.pages[start_page].extract_text() or ""
    # Simplified block splitting; adapt to your formatting heuristics
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    fund_blocks = []
    current = None

    for line in lines:
        # Detect new fund name (heuristic: all-caps or contains "Fund")
        if "Fund" in line or line.isupper():
            if current:
                fund_blocks.append(current)
            current = {"Fund Name": line, "Metrics": []}
        elif current:
            # Assume metric line format: "<Metric Name>: <Info>"
            if ":" in line:
                metric, info = line.split(":", 1)
                current["Metrics"].append({"Metric": metric.strip(), "Info": info.strip()})
            else:
                # fallback: append as ambiguous info
                current["Metrics"].append({"Metric": "Unknown", "Info": line})
    if current:
        fund_blocks.append(current)

    st.session_state["fund_blocks"] = fund_blocks
    st.markdown("**Step 3: Fund Scorecard Metrics**")
    st.write(f"Found {len(fund_blocks)} fund blocks.")
    st.json(fund_blocks)
    return fund_blocks

# === Step 5: Fund Performance / Ticker Matching ===
def step5_process_performance(pdf):
    start_page = st.session_state.get("toc_pages", {}).get("Fund Performance")
    if start_page is None:
        st.error("Fund Performance page not found in TOC.")
        return {}

    text = pdf.pages[start_page].extract_text() or ""
    # Simplistic extraction: look for ticker in parentheses after name
    # Build mapping from fund name to ticker using fuzzy logic as fallback
    fund_blocks = st.session_state.get("fund_blocks", [])
    name_to_ticker = {}

    for block in fund_blocks:
        name = block["Fund Name"]
        # naive search in performance text
        pattern = rf"{re.escape(name)}.*?\((\w{{1,5}})\)"
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            name_to_ticker[name] = m.group(1).upper()
        else:
            # fallback: try fuzzy matching against any ticker-like tokens
            # mock: no additional logic here; leave blank or implement your full heuristic
            name_to_ticker[name] = "UNKNOWN"

    st.session_state["fund_tickers"] = name_to_ticker
    st.markdown("**Step 5: Fund Performance / Ticker Extraction**")
    st.write(name_to_ticker)
    return name_to_ticker

# === Step 6: Factsheet Matching / Extraction ===
def step6_process_factsheets(pdf):
    factsheet_page = st.session_state.get("toc_pages", {}).get("Fund Factsheets")
    if factsheet_page is None:
        st.error("Fund Factsheets page not located.")
        return []

    # For simplicity assume first factsheet page contains summary tables
    raw = pdf.pages[factsheet_page].extract_text() or ""
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    # You'd replace this with your full fuzzy matching logic to associate
    # benchmark, category, assets, etc., with each fund.
    # Here we build a placeholder structure.
    fund_blocks = st.session_state.get("fund_blocks", [])
    facts = []
    for block in fund_blocks:
        facts.append({
            "Fund Name": block["Fund Name"],
            "Benchmark": "Placeholder Benchmark",
            "Category": "Placeholder Category",
            "Net Assets": "N/A",
            "Manager": "N/A",
            "Avg Market Cap": "N/A",
            "Expense Ratio": "N/A"
        })

    st.session_state["fund_factsheets"] = facts
    st.markdown("**Step 6: Factsheet Extraction / Matching**")
    st.write(facts)
    return facts


import re
import pandas as pd
import numpy as np
import streamlit as st

# --- helpers ---------------------------------------------------------
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

# --- build scorecard table with icons --------------------------------
def build_scorecard_tables(fund_blocks, tickers_map):
    scorecard_rows = []
    ips_summary = []

    for block in fund_blocks:
        name = block["Fund Name"]
        ticker = tickers_map.get(name, "UNKNOWN")
        metrics = {m["Metric"]: m["Info"] for m in block["Metrics"]}
        passive = is_passive(name)

        # raw values
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

        # Table 1: pass/fail icons
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

        # Overall IPS status logic
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

# --- usage in your app -----------------------------------------------
fund_blocks = st.session_state.get("fund_blocks", [])
fund_tickers = st.session_state.get("fund_tickers", {})

if not fund_blocks:
    st.warning("Run scorecard extraction first.")
else:
    st.subheader("Scorecard Metrics")  # Table 1
    df_scorecard, df_ips = build_scorecard_tables(fund_blocks, fund_tickers)
    st.dataframe(df_scorecard, use_container_width=True)

    st.subheader("IPS Summary")  # Table 2
    st.dataframe(df_ips, use_container_width=True)

