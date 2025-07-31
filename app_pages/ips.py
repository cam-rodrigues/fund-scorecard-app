import re
import pdfplumber
import pandas as pd
import numpy as np
import streamlit as st
from calendar import month_name
from rapidfuzz import fuzz

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

# === Step 1: Header / declared fund count ===
def process_page1(page_text):
    # Quarter/Year
    date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", page_text)
    quarter = extract_report_date(date_match.group(0)) if date_match else "Unknown"

    # Prepared for / by
    prepared_for = ""
    prepared_by = ""
    pf = re.search(r"Prepared For[:\s]*(.+)", page_text)
    pb = re.search(r"Prepared By[:\s]*(.+)", page_text)
    if pf:
        prepared_for = pf.group(1).strip()
    if pb:
        prepared_by = pb.group(1).strip()

    # Declared number of funds: look for patterns like "Total Funds: 5" or "5 Funds"
    declared_funds = None
    m = re.search(r"Total\s+Funds[:\s]*([0-9]+)", page_text, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"([0-9]+)\s+Funds", page_text, flags=re.IGNORECASE)
    if m:
        declared_funds = int(m.group(1))
    else:
        # fallback: try "Total Options" or similar
        m2 = re.search(r"Total\s+Options[:\s]*([0-9]+)", page_text, flags=re.IGNORECASE)
        if m2:
            declared_funds = int(m2.group(1))

    st.session_state["report_metadata"] = {
        "Quarter": quarter,
        "Prepared For": prepared_for or "N/A",
        "Prepared By": prepared_by or "N/A",
        "Declared Fund Count": declared_funds,
    }

# === Step 2: TOC locator ===
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

def step3_process_scorecard(pdf):
    toc = st.session_state.get("toc_pages", {})
    start_page = toc.get("Fund Scorecard")
    # Determine end of section: use next known section after scorecard (e.g., Fund Performance)
    end_page = toc.get("Fund Performance")
    if start_page is None:
        st.error("Scorecard start page not found.")
        return []

    # Collect text across the whole scorecard section
    pages_to_scan = []
    if end_page is not None and end_page > start_page:
        pages_to_scan = list(range(start_page, end_page))
    else:
        # fallback: scan start page plus next 2 if no clear boundary
        pages_to_scan = [p for p in range(start_page, min(start_page + 3, len(pdf.pages)))]

    raw_combined = ""
    for p in pages_to_scan:
        raw_combined += "\n" + (pdf.pages[p].extract_text() or "")

    lines = [l.strip() for l in raw_combined.split("\n") if l.strip()]

    fund_blocks = []
    current = None

    # Skip past the explanatory "Criteria Threshold" section by ignoring header until first real fund line
    # Heuristic for fund header: contains "Fund" and ends with "Criteria." or "Meets Watchlist Criteria." or similar
    fund_header_pattern = re.compile(r".*Fund.*(Meets Watchlist Criteria\.|Watchlist Criteria\.|Fund$)", flags=re.IGNORECASE)

    metric_line_pattern = re.compile(
        r"^(Manager Tenure|Excess Performance \(3Yr\)|Excess Performance \(5Yr\)|"
        r"Peer Return Rank \(3Yr\)|Peer Return Rank \(5Yr\)|Expense Ratio Rank|"
        r"Sharpe Ratio Rank \(3Yr\)|Sharpe Ratio Rank \(5Yr\)|R-Squared \(3Yr\)|"
        r"R-Squared \(5Yr\)|Sortino Ratio Rank \(3Yr\)|Sortino Ratio Rank \(5Yr\)|"
        r"Tracking Error Rank \(3Yr\)|Tracking Error Rank \(5Yr\))\s+(Pass|Review)\s*(.*)$",
        flags=re.IGNORECASE
    )

    for i, line in enumerate(lines):
        # Detect the start of a new fund
        if fund_header_pattern.match(line):
            if current:
                fund_blocks.append(current)
            # Clean name: strip off trailing descriptor like "Meets Watchlist Criteria."
            fund_name = re.sub(r"(Meets Watchlist Criteria\.?|Watchlist Criteria\.?)", "", line, flags=re.IGNORECASE).strip()
            current = {"Fund Name": fund_name, "Metrics": []}
            continue

        # Within a fund block, capture metrics lines with status
        if current:
            m = metric_line_pattern.match(line)
            if m:
                metric_name = m.group(1).strip()
                status = m.group(2).strip().capitalize()  # Pass / Review
                rest = m.group(3).strip()
                info = f"{status}" + (f": {rest}" if rest else "")
                current["Metrics"].append({"Metric": metric_name, "Info": info})
            else:
                # Sometimes explanation spills on next line; attach to last metric if exists and doesn't look like a new metric
                if current["Metrics"]:
                    last = current["Metrics"][-1]
                    # Avoid appending if this line looks like a new metric again
                    if not metric_line_pattern.match(line):
                        last["Info"] += " " + line

    if current:
        fund_blocks.append(current)

    declared = st.session_state.get("report_metadata", {}).get("Declared Fund Count")
    if declared is not None and len(fund_blocks) != declared:
        st.warning(
            f"Declared fund count is {declared} but extracted {len(fund_blocks)} fund blocks. "
            "Showing snippet for debugging."
        )
        sample = "\n".join(lines[:100])
        st.code(sample, language="text")

    if not fund_blocks:
        st.error("No fund blocks parsed. Dumping entire section for inspection.")
        st.subheader("Raw Scorecard Section Snippet")
        st.code("\n".join(lines[:300]), language="text")

    st.session_state["fund_blocks"] = fund_blocks



# === Step 5: Ticker extraction from performance page with fuzzy fallback ===
def step5_process_performance(pdf):
    start_page = st.session_state.get("toc_pages", {}).get("Fund Performance")
    if start_page is None or start_page >= len(pdf.pages):
        st.error("Fund Performance page not found.")
        return {}
    text = pdf.pages[start_page].extract_text() or ""
    fund_blocks = st.session_state.get("fund_blocks", [])
    name_to_ticker = {}

    # Build a list of candidate tickers by finding parentheses content that looks like tickers
    candidate_pairs = re.findall(r"([A-Za-z0-9 &\.\-]{3,60})\s*\((\w{1,5})\)", text)
    # Normalize fund names from performance section
    for block in fund_blocks:
        name = block["Fund Name"]
        found = False
        for perf_name, ticker in candidate_pairs:
            # fuzzy match the performance section name to the scorecard name
            score = fuzz.partial_ratio(name.lower(), perf_name.lower())
            if score >= 70:
                name_to_ticker[name] = ticker.upper()
                found = True
                break
        if not found:
            # direct pattern search for exact sequence
            pattern = rf"{re.escape(name)}.*?\((\w{{1,5}})\)"
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                name_to_ticker[name] = m.group(1).upper()
            else:
                name_to_ticker[name] = "UNKNOWN"

    st.session_state["fund_tickers"] = name_to_ticker

# === Step 6: Factsheet placeholder (can be extended) ===
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

# === Scorecard / IPS table builder ===
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

# === Entry point ===
def run():
    st.title("MPI Scorecard & IPS Metrics")
    uploaded = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if not uploaded:
        st.warning("Upload an MPI PDF to proceed.")
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1
        first_text = pdf.pages[0].extract_text() or ""
        process_page1(first_text)

        # Step 2
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

    # Display metadata
    st.subheader("Report Metadata")
    st.write(st.session_state.get("report_metadata", {}))

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
