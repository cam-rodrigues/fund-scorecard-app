# page_module.py

import streamlit as st
import pdfplumber
import re

def run():
    st.title("MPI Extraction")

    # Step 0: Upload MPI PDF
    uploaded_mpi = st.file_uploader("Upload your MPI PDF", type=["pdf"], key="mpi_upload")
    if uploaded_mpi is None:
        st.warning("Please upload an MPI PDF to continue.")
        return

    st.success(f"Uploaded: {uploaded_mpi.name}")

    # Open PDF once and reuse pages
    with pdfplumber.open(uploaded_mpi) as pdf:
        # === Step 1: Extract Header Information from First Page ===
        first_page_text = pdf.pages[0].extract_text() or ""

        # 1) Determine the quarter based on the date at top-left
        date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_page_text)
        quarter_map = {
            "3/31":  "Q1",
            "6/30":  "Q2",
            "9/30":  "Q3",
            "12/31": "Q4",
        }
        if date_match:
            full_date = date_match.group(1)                  # e.g. "3/31/2025"
            month_day = "/".join(full_date.split("/")[:2])   # e.g. "3/31"
            quarter = quarter_map.get(month_day, "Unknown")
            report_year = full_date.split("/")[-1]           # e.g. "2025"
            st.write(f"**Report Quarter:** {quarter} {report_year}")
        else:
            st.error("Could not determine report quarter from the first page.")

        # 2) Extract Total Options
        total_opts_match = re.search(r"Total Options\s*:\s*(\d+)", first_page_text)
        if total_opts_match:
            total_options = int(total_opts_match.group(1))
            st.write(f"**Total Investment Options:** {total_options}")
        else:
            st.error("Could not find 'Total Options' on the first page.")

        # 3) Extract Prepared For client name
        prepared_for_match = re.search(r"Prepared For\s*:\s*\n(.+)", first_page_text)
        if prepared_for_match:
            prepared_for = prepared_for_match.group(1).strip()
            st.write(f"**Prepared For:** {prepared_for}")
        else:
            st.error("Could not find 'Prepared For' on the first page.")

        # 4) Extract Prepared By name
        prepared_by_match = re.search(r"Prepared By\s*:\s*\n(.+)", first_page_text)
        if prepared_by_match:
            prepared_by = prepared_by_match.group(1).strip()
            st.write(f"**Prepared By:** {prepared_by}")
        else:
            st.error("Could not find 'Prepared By' on the first page.")

        # === Step 2: Locate Key Sections in Table of Contents (Page 2) ===
        toc_text = pdf.pages[1].extract_text() or ""
    
    # Split into lines for easier parsing
    toc_lines = toc_text.splitlines()

    # Define the section titles we care about
    sections = {
        "Fund Performance: Current vs. Proposed Comparison": None,
        "Fund Scorecard": None,
    }

    # Search each line for our section titles and capture the page number
    for line in toc_lines:
        for title in sections:
            pattern = rf"{re.escape(title)}\s+(\d+)"
            m = re.search(pattern, line)
            if m:
                sections[title] = int(m.group(1))

    # Display results
    if sections["Fund Performance: Current vs. Proposed Comparison"]:
        st.write(
            f"**Fund Performance** → page {sections['Fund Performance: Current vs. Proposed Comparison']}"
        )
    else:
        st.error("Could not find 'Fund Performance: Current vs. Proposed Comparison' in TOC.")

    if sections["Fund Scorecard"]:
        st.write(f"**Fund Scorecard** → page {sections['Fund Scorecard']}")
    else:
        st.error("Could not find 'Fund Scorecard' in TOC.")



# Step 3: Extract Fund Scorecard Metrics
import re
import streamlit as st
import pdfplumber
import pandas as pd

# Assume `uploaded_mpi` and `sections` (from Step 2) are available

# 1) Collect all pages of the Fund Scorecard section
start_idx = sections["Fund Scorecard"] - 1
scorecard_texts = []
with pdfplumber.open(uploaded_mpi) as pdf:
    for i in range(start_idx, len(pdf.pages)):
        text = pdf.pages[i].extract_text() or ""
        # Start when we hit the first "Fund Scorecard" page
        if "Fund Scorecard" in text or scorecard_texts:
            scorecard_texts.append(text)
            # Stop once the heading disappears (i.e. section ends)
            if i > start_idx and "Fund Scorecard" not in text:
                break

# 2) Parse out each fund and its metrics
records = []
current_fund = None

for page_text in scorecard_texts:
    for line in page_text.splitlines():
        # Skip boxes and headings
        if any(skip in line for skip in ["Criteria Threshold", "Fund Scorecard", "Investment Options"]):
            continue

        # Detect a new fund (bold subheading, no indent)
        if not line.startswith(" "):
            # Strip off any watchlist status text
            fund_name = re.split(r"Fund Meets|Fund has been placed", line)[0].strip()
            current_fund = fund_name

        # Detect metric lines (indented)
        else:
            m = re.match(r"\s*(.+?)\s+(Pass|Review)\s*(?:-\s*(.*))?$", line)
            if m and current_fund:
                metric, status, reason = m.group(1).strip(), m.group(2), m.group(3) or ""
                records.append({
                    "Fund Name": current_fund,
                    "Metric": metric,
                    "Status": status,
                    "Reason": reason.strip()
                })

# 3) Display as a table
df_scorecard = pd.DataFrame(records)
st.subheader("Fund Scorecard Metrics")
st.dataframe(df_scorecard)

