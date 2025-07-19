import streamlit as st
import pdfplumber
import re

def run():
    st.title("IPS Write-Up Tool")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_mpi")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        # === Step 1: Metadata ===
        st.subheader("Step 1: PDF Metadata")
        st.write("**Total Pages:**", len(pdf.pages))

#------------------------------------------------------------------------------------------------------------------

        # === Step 2: Page 1 Extraction ===
        st.subheader("Step 2: Pg 1")
        page1 = pdf.pages[0]
        text = page1.extract_text()

        # Determine Quarter
        quarter = "Unknown"
        if "3/31/20" in text:
            quarter = "Q1"
        elif "6/30/20" in text:
            quarter = "Q2"
        elif "9/30/20" in text:
            quarter = "Q3"
        elif "12/31/20" in text:
            quarter = "Q4"

        st.write("**Quarter:**", quarter)

        # Total Options
        total_match = re.search(r"Total Options:\s*(\d+)", text)
        total_options = total_match.group(1) if total_match else "Not found"
        st.write("**Total Investment Options:**", total_options)

        # Prepared For
        prepared_for_match = re.search(r"Prepared For:\s*\n(.+)", text)
        prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else "Not found"
        st.write("**Prepared For:**", prepared_for)

        # Prepared By
        prepared_by_match = re.search(r"Prepared By:\s*\n(.+)", text)
        prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else "Not found"
        st.write("**Prepared By:**", prepared_by)

#------------------------------------------------------------------------------------------------------------------

        # === Step 4: Pg 2 - Table of Contents ===
        st.subheader("Step 4: Pg 2 - Table of Contents")
        page2 = pdf.pages[1]
        text2 = page2.extract_text()

        fund_perf_pg = "Not found"
        fund_scorecard_pg = "Not found"

        for line in text2.split("\n"):
            if "Fund Performance: Current vs. Proposed Comparison" in line:
                match = re.search(r"(\d+)$", line)
                if match:
                    fund_perf_pg = int(match.group(1))
            if "Fund Scorecard" in line:
                match = re.search(r"(\d+)$", line)
                if match:
                    fund_scorecard_pg = int(match.group(1))

        st.write("**Fund Performance Page:**", fund_perf_pg)
        st.write("**Fund Scorecard Page:**", fund_scorecard_pg)

#------------------------------------------------------------------------------------------------------------------

        # === Step 5: Fund Scorecard Section ===
        st.subheader("Step 5: Fund Scorecard Section")

        metrics_data = []
        metrics_header = []
        fund_blocks = []

        # Read all pages starting from Fund Scorecard page
        for i in range(fund_scorecard_pg - 1, len(pdf.pages)):
            page = pdf.pages[i]
            text = page.extract_text()
            if not text or "Fund Scorecard" not in text:
                break

            lines = text.split("\n")

            # Capture Criteria Threshold section (appears once)
            if not metrics_header:
                for j in range(len(lines)):
                    if "Criteria Threshold" in lines[j]:
                        metrics_header = lines[j+1:j+15]
                        break

            # Capture fund blocks: look for lines starting with a metric, backtrack for fund name
            for j in range(len(lines)):
                if lines[j].startswith("Manager Tenure"):
                    fund_name = lines[j-1].strip()
                    fund_metrics = []
                    for k in range(j, j+14):
                        if k >= len(lines): break
                        metric_line = lines[k]
                        match = re.match(r"(.+?)\s+(Pass|Review)\s+(.*)", metric_line)
                        if match:
                            metric_name, status, reason = match.groups()
                            fund_metrics.append({
                                "Metric": metric_name.strip(),
                                "Status": status,
                                "Reason": reason.strip()
                            })
                    fund_blocks.append({
                        "Fund Name": fund_name,
                        "Metrics": fund_metrics
                    })

        # Display criteria header
        if metrics_header:
            st.markdown("**Criteria Threshold (14 Metrics):**")
            st.write(metrics_header)

        # Display fund blocks
        for block in fund_blocks:
            st.markdown(f"**{block['Fund Name']}**")
            for metric in block["Metrics"]:
                st.write(f"- {metric['Metric']}: **{metric['Status']}** – {metric['Reason']}")
                
#------------------------------------------------------------------------------------------------------------------
