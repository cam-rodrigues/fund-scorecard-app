import streamlit as st
import pdfplumber
import re
from difflib import SequenceMatcher
from difflib import SequenceMatcher, get_close_matches
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO
from io import StringIO
from rapidfuzz import fuzz

def run():
    st.set_page_config(page_title="Write-Up Info Tool", layout="wide")
    st.title("Write-Up Info Tool")

#--------------------------------------------------------------------------------------------
    
    # === Step 0: Upload MPI PDF ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")

    if not uploaded_file:
        st.warning("Please upload an MPI PDF to begin.")
        return

#--------------------------------------------------------------------------------------------
   
    # === Step 1: Page 1 ===
    with pdfplumber.open(uploaded_file) as pdf:
        first_page_text = pdf.pages[0].extract_text()

    # Match date pattern (e.g. 3/31/2024)
    date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_page_text)
    if date_match:
        date_str = date_match.group(1)
        year = date_str[-4:]
        if date_str.startswith("3/31"):
            quarter = f"Q1, {year}"
        elif date_str.startswith("6/30"):
            quarter = f"Q2, {year}"
        elif date_str.startswith("9/30"):
            quarter = f"Q3, {year}"
        elif date_str.startswith("12/31"):
            quarter = f"Q4, {year}"
        else:
            quarter = "Unknown"
    else:
        date_str = "Not found"
        quarter = "Unknown"

    # Save to session state and display
    st.session_state["report_quarter"] = quarter
    st.subheader("Step 1: Quarter Detected")
    st.write(f"Detected Date: **{date_str}**")
    st.write(f"Determined Quarter: **{quarter}**")

#--------------------------------------------------------------------------------------------
  
    # === Step 1.5: Extract Additional Page 1 Info ===

    # Extract Total Options
    total_match = re.search(r"Total Options:\s*(\d+)", first_page_text)
    total_options = int(total_match.group(1)) if total_match else None

    # Extract "Prepared For"
    prepared_for_match = re.search(r"Prepared For:\s*\n(.*)", first_page_text)
    prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else "Not found"

    # Extract "Prepared By"
    prepared_by_match = re.search(r"Prepared By:\s*\n(.*)", first_page_text)
    prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else "Not found"

    # Save to session state
    st.session_state["total_options"] = total_options
    st.session_state["prepared_for"] = prepared_for
    st.session_state["prepared_by"] = prepared_by

    # Display
    st.subheader("Step 1.5: Page 1 Summary Info")
    st.write(f"Total Options: **{total_options}**" if total_options is not None else "Total Options not found.")
    st.write(f"Prepared For: **{prepared_for}**")
    st.write(f"Prepared By: **{prepared_by}**")

#--------------------------------------------------------------------------------------------
    # === Step 2: Table of Contents (Page 2) ===
    toc_text = pdf.pages[1].extract_text()

    # Pattern to capture section titles and page numbers (e.g., "Fund Scorecard ............................................. 7")
    toc_entries = re.findall(r"(Fund Performance: Current vs\. Proposed Comparison|Fund Scorecard|Fund Factsheets).*?(\d{1,3})", toc_text)

    # Initialize storage
    toc_pages = {
        "Fund Performance": None,
        "Fund Scorecard": None,
        "Fund Factsheets": None
    }

    # Match and save to session_state
    for title, page in toc_entries:
        page_num = int(page)
        if "Fund Performance" in title:
            toc_pages["Fund Performance"] = page_num
        elif "Fund Scorecard" in title:
            toc_pages["Fund Scorecard"] = page_num
        elif "Fund Factsheets" in title:
            toc_pages["Fund Factsheets"] = page_num

    st.session_state["toc_pages"] = toc_pages

    # Display
    st.subheader("Step 2: Table of Contents")
    st.write(f"Fund Performance: **Page {toc_pages['Fund Performance']}**" if toc_pages["Fund Performance"] else "Fund Performance section not found.")
    st.write(f"Fund Scorecard: **Page {toc_pages['Fund Scorecard']}**" if toc_pages["Fund Scorecard"] else "Fund Scorecard section not found.")
    st.write(f"Fund Factsheets: **Page {toc_pages['Fund Factsheets']}**" if toc_pages["Fund Factsheets"] else "Fund Factsheets section not found.")

#--------------------------------------------------------------------------------------------

    # === Step 3: Fund Scorecard Section (Extract & Tabulate Metrics + Funds) ===
    fund_scorecard_pg = toc_pages.get("Fund Scorecard")
    if not fund_scorecard_pg:
        st.error("Fund Scorecard section page number not found in Table of Contents.")
        return

    # === Extract Criteria Threshold (first page of Fund Scorecard section) ===
    first_scorecard_text = pdf.pages[fund_scorecard_pg - 1].extract_text()
    criteria_match = re.search(r"Criteria Threshold\s*\n((?:.*\n){10,20})", first_scorecard_text)
    if criteria_match:
        criteria_block = criteria_match.group(1)
        metrics_list = [line.strip() for line in criteria_block.strip().split("\n") if line.strip()]
    else:
        metrics_list = []

    metrics_df = pd.DataFrame({
        "Metric #": list(range(1, len(metrics_list) + 1)),
        "Fund Scorecard Metric": metrics_list
    }) if metrics_list else pd.DataFrame(columns=["Metric #", "Fund Scorecard Metric"])

    # Save Criteria Threshold
    st.session_state["fund_scorecard_metrics"] = metrics_list
    st.session_state["fund_scorecard_table"] = metrics_df

    # Display Threshold Table
    st.subheader("Step 3: Fund Scorecard Metrics Table")
    if not metrics_list:
        st.write("No metrics found under 'Criteria Threshold'.")
    else:
        st.dataframe(metrics_df, use_container_width=True)

    # === Step 3.5: Extract Investment Option Metrics into Separate Tables (Allow Incomplete Funds) ===
    st.subheader("Step 3.5: Individual Investment Option Tables")

    fund_blocks = []
    fund_status_pattern = re.compile(
        r"\s+(Fund Meets Watchlist Criteria\.|Fund has been placed on watchlist for not meeting.+)", re.IGNORECASE)

    fund_scorecard_start = toc_pages.get("Fund Scorecard")
    fund_factsheets_start = toc_pages.get("Fund Factsheets")
    last_page_index = fund_factsheets_start - 2 if fund_factsheets_start else len(pdf.pages) - 1

    for i in range(fund_scorecard_start - 1, last_page_index + 1):
        page = pdf.pages[i]
        text = page.extract_text()
        if not text:
            continue

        lines = text.split("\n")
        for j in range(len(lines)):
            if lines[j].startswith("Manager Tenure") and j > 0:
                raw_fund_line = lines[j - 1].strip()
                fund_name = fund_status_pattern.sub("", raw_fund_line).strip()
                if "criteria threshold" in fund_name.lower():
                    continue

                fund_metrics = []
                for k in range(j, j + 14):
                    if k >= len(lines): break
                    metric_line = lines[k].strip()
                    match = re.match(r"(.+?)\s+(Pass|Review)\s*[-–]?\s*(.*)", metric_line)
                    if match:
                        metric_name, status, reason = match.groups()
                    else:
                        # Fallback if match failed
                        parts = metric_line.split(" ", 1)
                        metric_name = parts[0] if parts else "Unknown Metric"
                        status = "N/A"
                        reason = parts[1].strip() if len(parts) > 1 else ""

                    fund_metrics.append({
                        "Metric": metric_name.strip(),
                        "Status": status.strip(),
                        "Reason": reason.strip()
                    })

                # Save even if partial metrics
                fund_blocks.append({
                    "Fund Name": fund_name,
                    "Metrics": fund_metrics
                })

    # Save to session state
    st.session_state["fund_blocks"] = fund_blocks

    # Display each fund as a table
    for block in fund_blocks:
        st.markdown(f"### {block['Fund Name']}")
        df = pd.DataFrame(block["Metrics"])
        st.dataframe(df, use_container_width=True)

    # === Step 3.6: Double Check Fund Count ===
    st.subheader("Step 3.6: Investment Option Count Check")

    declared_total = st.session_state.get("total_options")
    actual_total = len(fund_blocks)

    st.write(f"Declared in Page 1: **{declared_total}**")
    st.write(f"Found in Fund Scorecard: **{actual_total}**")

    if declared_total is None:
        st.warning("No declared total found on Page 1 to compare against.")
    elif declared_total == actual_total:
        st.success("✅ The number of Investment Options matches the declared total.")
    else:
        st.error("❌ Mismatch between declared and actual number of Investment Options.")

#--------------------------------------------------------------------------------------------

    # === Step 4: IPS Investment Criteria Definitions ===
    st.subheader("Step 4: IPS Investment Criteria Setup")

    IPS_CRITERIA = [
        {
            "Name": "Manager Tenure ≥ 3 years",
            "Active Metric": "Manager Tenure",
            "Passive Metric": "Manager Tenure",
            "Always Include": True
        },
        {
            "Name": "3-Year Performance > Benchmark / 3-Year R² > 95%",
            "Active Metric": "3-Year Performance",
            "Passive Metric": "3-Year R²",
            "Always Include": True
        },
        {
            "Name": "3-Year Performance > 50% of Peers",
            "Active Metric": "3-Year Performance vs Peers",
            "Passive Metric": "3-Year Performance vs Peers",
            "Always Include": True
        },
        {
            "Name": "3-Year Sharpe Ratio > 50% of Peers",
            "Active Metric": "3-Year Sharpe Ratio",
            "Passive Metric": "3-Year Sharpe Ratio",
            "Always Include": True
        },
        {
            "Name": "3-Year Sortino Ratio > 50% of Peers / 3-Year Tracking Error < 90% of Peers",
            "Active Metric": "3-Year Sortino Ratio",
            "Passive Metric": "3-Year Tracking Error Rank (5Yr)",
            "Always Include": True
        },
        {
            "Name": "5-Year Performance > Benchmark / 5-Year R² > 95%",
            "Active Metric": "5-Year Performance",
            "Passive Metric": "5-Year R²",
            "Always Include": True
        },
        {
            "Name": "5-Year Performance > 50% of Peers",
            "Active Metric": "5-Year Performance vs Peers",
            "Passive Metric": "5-Year Performance vs Peers",
            "Always Include": True
        },
        {
            "Name": "5-Year Sharpe Ratio > 50% of Peers",
            "Active Metric": "5-Year Sharpe Ratio",
            "Passive Metric": "5-Year Sharpe Ratio",
            "Always Include": True
        },
        {
            "Name": "5-Year Sortino Ratio > 50% of Peers / 5-Year Tracking Error < 90% of Peers",
            "Active Metric": "5-Year Sortino Ratio",
            "Passive Metric": "5-Year Tracking Error Rank (5Yr)",
            "Always Include": True
        },
        {
            "Name": "Expense Ratio < 50% of Peers",
            "Active Metric": "Expense Ratio",
            "Passive Metric": "Expense Ratio",
            "Always Include": True
        },
        {
            "Name": "Investment Style aligns with fund objectives",
            "Active Metric": "Investment Style",
            "Passive Metric": "Investment Style",
            "Always Include": True
        }
    ]

    # Save to session state
    st.session_state["ips_criteria"] = IPS_CRITERIA

    # Display in app for reference
    st.markdown("### IPS Investment Criteria")
    for i, c in enumerate(IPS_CRITERIA, start=1):
        st.markdown(f"**{i}.** {c['Name']}")

    # === Step 4.5: IPS Investment Criteria Screening ===
    st.subheader("Step 4.5: IPS Investment Criteria Screening")

    ips_criteria = [
        "Manager Tenure ≥ 3 years",
        "3-Year Performance > Benchmark / +3-Year R² > 95%",
        "3-Year Performance > 50% of Peers",
        "3-Year Sharpe Ratio > 50% of Peers",
        "3-Year Sortino Ratio > 50% of Peers / +3-Year Tracking Error < 90% of Peers",
        "5-Year Performance > Benchmark / +5-Year R² > 95%",
        "5-Year Performance > 50% of Peers",
        "5-Year Sharpe Ratio > 50% of Peers",
        "5-Year Sortino Ratio > 50% of Peers / +5-Year Tracking Error < 90% of Peers",
        "Expense Ratio < 50% of Peers",
        "Investment Style aligns with fund objectives"
    ]

    st.markdown("**IPS Investment Criteria:**")
    for i, crit in enumerate(ips_criteria, 1):
        st.markdown(f"{i}. {crit}")

    def map_metric_names(fund_type):
        if fund_type == "Passive":
            return [
                "Manager Tenure",
                "R² (3Yr)",
                "Return Rank (3Yr)",
                "Sharpe Ratio Rank (3Yr)",
                "Tracking Error Rank (3Yr)",
                "R² (5Yr)",
                "Return Rank (5Yr)",
                "Sharpe Ratio Rank (5Yr)",
                "Tracking Error Rank (5Yr)",
                "Expense Ratio Rank",
                "Investment Style"
            ]
        else:
            return [
                "Manager Tenure",
                "Excess Performance (3Yr)",
                "Return Rank (3Yr)",
                "Sharpe Ratio Rank (3Yr)",
                "Sortino Ratio Rank (3Yr)",
                "Excess Performance (5Yr)",
                "Return Rank (5Yr)",
                "Sharpe Ratio Rank (5Yr)",
                "Sortino Ratio Rank (5Yr)",
                "Expense Ratio Rank",
                "Investment Style"
            ]

    if "step8_results" not in st.session_state:
        st.session_state["step8_results"] = []

    fund_blocks = st.session_state.get("fund_blocks", [])

    for block in fund_blocks:
        fund_name = block["Fund Name"]
        fund_type = "Passive" if "bitcoin" in fund_name.lower() else "Active"
        expected_metrics = map_metric_names(fund_type)

        # Build lookup: {Metric → Pass/Review}
        metric_lookup = {m["Metric"]: m["Status"] for m in block["Metrics"]}

        # Build full table w/ label, status, and pass/fail
        table_rows = []
        ips_results = []

        for i, label in enumerate(expected_metrics):
            status = metric_lookup.get(label, "Review")
            result = "Pass" if (i == 10 or status == "Pass") else "Fail"  # Last one always Pass
            ips_results.append(result)
            table_rows.append({
                "Metric": ips_criteria[i],
                "Status": status
            })

        # Count fails
        fail_count = ips_results.count("Fail")
        if fail_count <= 4:
            overall_status = "Passed IPS Screen"
        elif fail_count == 5:
            overall_status = "Informal Watch (IW)"
        else:
            overall_status = "Formal Watch (FW)"

        st.session_state["step8_results"].append({
            "Fund Name": fund_name,
            "Fund Type": fund_type,
            "IPS Metrics": table_rows,
            "Overall IPS Status": overall_status
        })

        # Display per-fund table
        st.markdown(f"### {fund_name}")
        st.write(f"**Fund Type:** {fund_type}")
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True)
        st.write(f"**Overall IPS Status:** `{overall_status}`")

#-------------------------------------------------------------------------------------------

    # === Step 5: Fund Performance Section Navigation ===
    st.subheader("Step 5: Fund Performance: Current vs. Proposed Comparison")
    
    toc_pages = st.session_state.get("toc_pages", {})
    fund_perf_pg = toc_pages.get("Fund Performance")
    
    if not fund_perf_pg:
        st.error("❌ 'Fund Performance' section page not found in TOC.")
    else:
        with pdfplumber.open(uploaded_file) as pdf:
            fund_perf_text = pdf.pages[fund_perf_pg - 1].extract_text()
    
        if "Fund Performance: Current vs. Proposed Comparison" not in fund_perf_text:
            st.warning("⚠️ The expected section heading was not found on the starting page. Please double-check manually.")
        else:
            st.success("✔️ Found the Fund Performance section heading.")

    
    # === Step 5.5: Match Investment Option Names & Extract Tickers ===
    st.subheader("Step 5.5: Match Investment Option Names Between Sections")
    
    # Pull fund names from Scorecard section
    fund_blocks = st.session_state.get("fund_blocks", [])
    scorecard_names = [block["Fund Name"] for block in fund_blocks]
    
    toc_pages = st.session_state.get("toc_pages", {})
    start_page = toc_pages.get("Fund Performance")
    end_page = toc_pages.get("Fund Scorecard")
    
    if not start_page or not end_page:
        st.error("Missing TOC page numbers for Fund Performance or Fund Scorecard section.")
    else:
        # Step 1: Gather all lines between Fund Performance and Fund Scorecard pages
        perf_lines = []
        with pdfplumber.open(uploaded_file) as pdf:
            for i in range(start_page - 1, end_page - 1):  # PDF is 0-indexed
                text = pdf.pages[i].extract_text()
                if text:
                    perf_lines.extend(text.split("\n"))
    
        # Step 2: Fuzzy match Scorecard names to Performance lines
        match_data = []
        for score_name in scorecard_names:
            best_score = 0
            best_line = ""
            best_ticker = ""
            for line in perf_lines:
                # Skip lines that are too short or clearly not fund names
                if len(line.strip()) < 10 or not re.search(r"\b[A-Z]{5}\b", line):
                    continue
    
                similarity = fuzz.token_sort_ratio(score_name.lower(), line.lower())
                if similarity > best_score:
                    best_score = similarity
                    ticker_match = re.search(r"\b[A-Z]{5}\b", line)
                    best_ticker = ticker_match.group(0) if ticker_match else ""
                    best_line = line.strip()
    
            match_data.append({
                "Fund Scorecard Name": score_name,
                "Ticker": best_ticker,
                "Matched Line": best_line,
                "Match Score": best_score,
                "Matched": "✅" if best_score >= 60 else "❌"
            })
    
        # Save results
        st.session_state["fund_performance_data"] = match_data
    
        # Display results
        df_matches = pd.DataFrame(match_data)
        st.dataframe(df_matches)
    
        matched_count = sum(1 for m in match_data if m["Matched"] == "✅")
        total_count = len(match_data)
        st.write(f"✅ Matched {matched_count} of {total_count} fund names to Performance section.")
        if matched_count != total_count:
            st.error("❌ Mismatch in number of matched funds. Check for missing or misnamed items.")
        else:
            st.success("✔️ All funds successfully matched.")

#-------------------------------------------------------------------------------------------

    # === Step 6: Fund Factsheets Section ===
    st.subheader("Step 6: Fund Factsheets Section")

    toc_pages = st.session_state.get("toc_pages", {})
    performance_data = st.session_state.get("fund_performance_data", [])
    total_declared = st.session_state.get("total_options")

    factsheet_start = toc_pages.get("Fund Factsheets")

    if not factsheet_start:
        st.error("❌ 'Fund Factsheets' page number not found in TOC.")
    else:
        with pdfplumber.open(uploaded_file) as pdf:
            matched_factsheets = []

            for i in range(factsheet_start - 1, len(pdf.pages)):
                page = pdf.pages[i]

                # Extract top header using words
                words = page.extract_words(use_text_flow=True)
                header_words = [w['text'] for w in words if w['top'] < 100]
                first_line = " ".join(header_words).strip()

                if not first_line:
                    continue

                # Match using Fund Performance names + tickers
                best_match_score = 0
                matched_name = ""
                matched_ticker = ""

                for perf in performance_data:
                    label = f"{perf['Fund Scorecard Name']} {perf['Ticker']}".strip()
                    score = fuzz.token_sort_ratio(first_line.lower(), label.lower())
                    if score > best_match_score:
                        best_match_score = score
                        matched_name = perf["Fund Scorecard Name"]
                        matched_ticker = perf["Ticker"]

                # Extract metadata fields
                def extract_field(label, text, stop_at=None):
                    try:
                        start = text.index(label) + len(label)
                        rest = text[start:]
                        if stop_at and stop_at in rest:
                            return rest[:rest.index(stop_at)].strip()
                        return rest.strip().split()[0]
                    except Exception:
                        return ""

                benchmark = extract_field("Benchmark:", first_line, "Category:")
                category = extract_field("Category:", first_line, "Net Assets:")
                net_assets = extract_field("Net Assets:", first_line, "Manager Name:")
                manager = extract_field("Manager Name:", first_line, "Avg. Market Cap:")
                avg_cap = extract_field("Avg. Market Cap:", first_line, "Expense Ratio:")
                expense = extract_field("Expense Ratio:", first_line)

                matched_factsheets.append({
                    "Page #": i + 1,
                    "Matched Fund Name": matched_name,
                    "Matched Ticker": matched_ticker,
                    "Benchmark": benchmark,
                    "Category": category,
                    "Net Assets": net_assets,
                    "Manager Name": manager,
                    "Avg. Market Cap": avg_cap,
                    "Expense Ratio": expense,
                    "Match Score": best_match_score,
                    "Matched": "✅" if best_match_score >= 60 else "❌"
                })

        # Save to session_state
        st.session_state["fund_factsheets_data"] = matched_factsheets

        # Display
        df_facts = pd.DataFrame(matched_factsheets)
        st.dataframe(df_facts)

        matched_count = sum(1 for f in matched_factsheets if f["Matched"] == "✅")
        total_pages = len(matched_factsheets)

        st.write(f"✅ Matched {matched_count} of {total_pages} factsheet pages to Fund Performance funds.")

        if matched_count == total_declared:
            st.success(f"✅ All {matched_count} funds matched the declared Total Options from Page 1.")
        else:
            st.error(f"❌ Mismatch: Page 1 declared {total_declared}, but only matched {matched_count}.")
