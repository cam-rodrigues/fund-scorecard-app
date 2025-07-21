import streamlit as st
import pandas as pd
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Write-Up Info Tool", layout="wide")
    st.title("Write-Up Info Tool")

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

    # === Step 4: IPS Investment Criteria Screening ===
    st.subheader("Step 4: IPS Investment Criteria Screening")

    IPS_CRITERIA = [
        "Manager Tenure ≥ 3 years",
        "*3-Year Performance > Benchmark / +3-Year R² > 95%",
        "3-Year Performance > 50% of Peers",
        "3-Year Sharpe Ratio > 50% of Peers",
        "*3-Year Sortino Ratio > 50% of Peers / +3-Year Tracking Error < 90% of Peers",
        "*5-Year Performance > Benchmark / +5-Year R² > 95%",
        "5-Year Performance > 50% of Peers",
        "5-Year Sharpe Ratio > 50% of Peers",
        "*5-Year Sortino Ratio > 50% of Peers / +5-Year Tracking Error < 90% of Peers",
        "Expense Ratio < 50% of Peers",
        "Investment Style aligns with fund objectives"
    ]

    # Save for later use
    st.session_state["ips_criteria_text"] = IPS_CRITERIA

    ips_results = []

    for block in st.session_state.get("fund_blocks", []):
        fund_name = block["Fund Name"]
        metrics = block["Metrics"]

        # Determine Active or Passive
        is_passive = "bitcoin" in fund_name.lower()

        # Map metrics to names for lookup
        metric_lookup = {m["Metric"]: m["Status"] for m in metrics}

        # Evaluate IPS metrics
        ips_statuses = []

        for i, crit in enumerate(IPS_CRITERIA):
            status = "Fail"

            if i == 0:
                status = metric_lookup.get("Manager Tenure", "Fail")

            elif i == 1:
                # Active uses "3-Year Performance", Passive uses "3-Year R²"
                if is_passive:
                    status = metric_lookup.get("3-Year R²", "Fail")
                else:
                    status = metric_lookup.get("3-Year Performance", "Fail")

            elif i == 2:
                status = metric_lookup.get("3-Year Performance vs Peers", "Fail")

            elif i == 3:
                status = metric_lookup.get("3-Year Sharpe Ratio", "Fail")

            elif i == 4:
                if is_passive:
                    status = metric_lookup.get("3-Year Tracking Error Rank (5Yr)", "Fail")
                else:
                    status = metric_lookup.get("3-Year Sortino Ratio", "Fail")

            elif i == 5:
                if is_passive:
                    status = metric_lookup.get("5-Year R²", "Fail")
                else:
                    status = metric_lookup.get("5-Year Performance", "Fail")

            elif i == 6:
                status = metric_lookup.get("5-Year Performance vs Peers", "Fail")

            elif i == 7:
                status = metric_lookup.get("5-Year Sharpe Ratio", "Fail")

            elif i == 8:
                if is_passive:
                    status = metric_lookup.get("5-Year Tracking Error Rank (5Yr)", "Fail")
                else:
                    status = metric_lookup.get("5-Year Sortino Ratio", "Fail")

            elif i == 9:
                status = metric_lookup.get("Expense Ratio", "Fail")

            elif i == 10:
                status = "Pass"  # Always Pass

            if status not in ["Pass", "Review"]:
                status = "Fail"

            ips_statuses.append(status)

        # Count number of failed metrics (non-"Pass")
        num_failed = sum(1 for s in ips_statuses if s != "Pass")

        if num_failed <= 4:
            overall_status = "Passed IPS Screen"
        elif num_failed == 5:
            overall_status = "Informal Watch"
        else:
            overall_status = "Formal Watch"

        ips_results.append({
            "Fund Name": fund_name,
            "Passive": is_passive,
            "IPS Metric Statuses": ips_statuses,
            "Failed IPS Metrics": num_failed,
            "Overall IPS Status": overall_status
        })

    # Save results
    st.session_state["ips_results"] = ips_results

    # Display summary table
    st.write("### IPS Screening Results Summary")
    summary_df = pd.DataFrame([{
        "Fund Name": r["Fund Name"],
        "Passive": r["Passive"],
        "Fails": r["Failed IPS Metrics"],
        "Overall IPS Status": r["Overall IPS Status"]
    } for r in ips_results])
    st.dataframe(summary_df, use_container_width=True)
