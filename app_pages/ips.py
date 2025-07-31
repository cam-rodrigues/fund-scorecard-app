# page_module.py

import streamlit as st
import pdfplumber
import re
import pandas as pd

def run():
    st.title("MPI Extraction")

    # Step 0: Upload MPI PDF
    uploaded_mpi = st.file_uploader("Upload your MPI PDF", type=["pdf"], key="mpi_upload")
    if uploaded_mpi is None:
        st.warning("Please upload an MPI PDF to continue.")
        return
    st.success(f"Uploaded: {uploaded_mpi.name}")

    # Open the PDF once and reuse
    with pdfplumber.open(uploaded_mpi) as pdf:
        # === Step 1: Header Info (page 1) ===
        first_page_text = pdf.pages[0].extract_text() or ""
        date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_page_text)
        quarter_map = {"3/31":"Q1","6/30":"Q2","9/30":"Q3","12/31":"Q4"}
        if date_match:
            full_date = date_match.group(1)
            month_day = "/".join(full_date.split("/")[:2])
            quarter = quarter_map.get(month_day, "Unknown")
            year = full_date.split("/")[-1]
            st.write(f"**Report Quarter:** {quarter} {year}")
        else:
            st.error("Could not determine report quarter.")

        total_opts = re.search(r"Total Options\s*:\s*(\d+)", first_page_text)
        if total_opts:
            st.write(f"**Total Investment Options:** {int(total_opts.group(1))}")
        else:
            st.error("Could not find 'Total Options'.")

        pf = re.search(r"Prepared For\s*:\s*\n(.+)", first_page_text)
        if pf:
            st.write(f"**Prepared For:** {pf.group(1).strip()}")
        else:
            st.error("Could not find 'Prepared For'.")

        pb = re.search(r"Prepared By\s*:\s*\n(.+)", first_page_text)
        if pb:
            st.write(f"**Prepared By:** {pb.group(1).strip()}")
        else:
            st.error("Could not find 'Prepared By'.")

        # === Step 2: Table of Contents (page 2) ===
        toc_text = pdf.pages[1].extract_text() or ""
    toc_lines = toc_text.splitlines()

    # Look up the page numbers for the two sections
    sections = {"Fund Performance": None, "Fund Scorecard": None}
    for line in toc_lines:
        m1 = re.search(r"Fund Performance: Current vs\. Proposed Comparison\s+(\d+)", line)
        if m1:
            sections["Fund Performance"] = int(m1.group(1))
        m2 = re.search(r"Fund Scorecard\s+(\d+)", line)
        if m2:
            sections["Fund Scorecard"] = int(m2.group(1))

    if sections["Fund Performance"]:
        st.write(f"**Fund Performance** → page {sections['Fund Performance']}")
    else:
        st.error("Could not find 'Fund Performance' in TOC.")

    if sections["Fund Scorecard"]:
        st.write(f"**Fund Scorecard** → page {sections['Fund Scorecard']}")
    else:
        st.error("Could not find 'Fund Scorecard' in TOC.")
        return  # can't proceed without scorecard page

    # === Step 3: Extract Fund Scorecard Metrics ===
    scorecard_start = sections["Fund Scorecard"] - 1
    records = []
    with pdfplumber.open(uploaded_mpi) as pdf:
        for i in range(scorecard_start, len(pdf.pages)):
            text = pdf.pages[i].extract_text() or ""
            # stop when we reach a new major section (no longer in scorecard)
            if i > scorecard_start and "Fund Scorecard" not in text:
                break
            for line in text.splitlines():
                # skip headings and threshold box
                if any(skip in line for skip in ["Fund Scorecard", "Investment Options", "Criteria Threshold"]):
                    continue
                # new fund heading (not indented)
                if not line.startswith(" "):
                    current_fund = re.split(r"Fund Meets|Fund has been placed", line)[0].strip()
                else:
                    m = re.match(r"\s*(.+?)\s+(Pass|Review)\s*(?:-\s*(.*))?$", line)
                    if m:
                        metric = m.group(1).strip()
                        status = m.group(2)
                        reason = (m.group(3) or "").strip()
                        records.append({
                            "Fund Name": current_fund,
                            "Metric": metric,
                            "Status": status,
                            "Reason": reason
                        })

    # Display results
    if records:
        df = pd.DataFrame(records)
        st.subheader("Fund Scorecard Metrics")
        st.dataframe(df)
    else:
        st.error("No scorecard metrics found.")
