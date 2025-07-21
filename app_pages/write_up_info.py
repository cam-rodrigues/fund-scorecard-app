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

    # === Step 3.5: Extract Investment Option Metrics into Separate Tables ===
    st.subheader("Step 3.5: Individual Investment Option Tables")

    fund_blocks = []

    fund_status_pattern = re.compile(
        r"\s+(Fund Meets Watchlist Criteria\.|Fund has been placed on watchlist for not meeting.+)", re.IGNORECASE)

    for i in range(fund_scorecard_pg - 1, len(pdf.pages)):
        page = pdf.pages[i]
        text = page.extract_text()
        if not text or "Fund Scorecard" not in text:
            break

        lines = text.split("\n")
        for j in range(len(lines)):
            if lines[j].startswith("Manager Tenure") and j > 0:
                raw_fund_line = lines[j - 1].strip()
                fund_name = fund_status_pattern.sub("", raw_fund_line).strip()
                if "criteria threshold" in fund_name.lower():
                    continue  # skip bad block

                fund_metrics = []
                for k in range(j, j + 14):
                    if k >= len(lines): break
                    metric_line = lines[k]
                    match = re.match(r"(.+?)\s+(Pass|Review)\s*[-–]?\s*(.*)", metric_line)
                    if match:
                        metric_name, status, reason = match.groups()
                        fund_metrics.append({
                            "Metric": metric_name.strip(),
                            "Status": status.strip(),
                            "Reason": reason.strip()
                        })

                if len(fund_metrics) == 14:
                    fund_blocks.append({
                        "Fund Name": fund_name,
                        "Metrics": fund_metrics
                    })

    # Save fund_blocks to session_state
    st.session_state["fund_blocks"] = fund_blocks

    # Display a separate table per fund
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

