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

    # Open PDF to extract header and TOC
    with pdfplumber.open(uploaded_mpi) as pdf:
        # === Step 1: Header Info (page 1) ===
        first_text = pdf.pages[0].extract_text() or ""
        date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_text)
        quarter_map = {"3/31":"Q1","6/30":"Q2","9/30":"Q3","12/31":"Q4"}
        if date_match:
            d = date_match.group(1)
            q = quarter_map.get("/".join(d.split("/")[:2]), "Unknown")
            year = d.split("/")[-1]
            st.write(f"**Report Quarter:** {q} {year}")
        else:
            st.error("Could not determine report quarter.")

        opts = re.search(r"Total Options\s*:\s*(\d+)", first_text)
        st.write(f"**Total Investment Options:** {int(opts.group(1)) if opts else 'N/A'}")

        pf = re.search(r"Prepared For\s*:\s*\n(.+)", first_text)
        st.write(f"**Prepared For:** {pf.group(1).strip() if pf else 'N/A'}")

        pb = re.search(r"Prepared By\s*:\s*\n(.+)", first_text)
        st.write(f"**Prepared By:** {pb.group(1).strip() if pb else 'N/A'}")

        # === Step 2: Table of Contents (page 2) ===
        toc_text = pdf.pages[1].extract_text() or ""
    toc_lines = toc_text.splitlines()

    sections = {"Fund Performance": None, "Fund Scorecard": None}
    for line in toc_lines:
        m1 = re.search(r"Fund Performance: Current vs\.? Proposed Comparison\s+(\d+)", line)
        if m1:
            sections["Fund Performance"] = int(m1.group(1))
        m2 = re.search(r"Fund Scorecard\s+(\d+)", line)
        if m2:
            sections["Fund Scorecard"] = int(m2.group(1))

    if not sections["Fund Scorecard"]:
        st.error("'Fund Scorecard' not found in TOC.")
        return
    st.write(f"**Fund Scorecard** starts on page {sections['Fund Scorecard']}")

    # === Step 3: Extract Scorecard Metrics ===
    start_page = sections["Fund Scorecard"] - 1
    records = []
    current_fund = None
    skip_keys = ["Fund Scorecard", "Investment Options", "Criteria Threshold"]

    with pdfplumber.open(uploaded_mpi) as pdf:
        for i in range(start_page, len(pdf.pages)):
            text = pdf.pages[i].extract_text() or ""
            # stop if we hit next major section (optional)
            # if i > start_page and "Fund Factsheets" in text:
            #     break
            for line in text.splitlines():
                if any(key in line for key in skip_keys):
                    continue
                if " Pass" in line or " Review" in line:
                    if " Pass" in line:
                        name, rest = line.split(" Pass", 1)
                        status = "Pass"
                    else:
                        name, rest = line.split(" Review", 1)
                        status = "Review"
                    metric = name.strip()
                    reason = rest.lstrip(" -–—:").strip()
                    records.append({
                        "Fund Name": current_fund,
                        "Metric": metric,
                        "Status": status,
                        "Reason": reason
                    })
                else:
                    # treat non-empty, non-skipped lines as fund headings
                    if line.strip():
                        current_fund = line.strip()

    if records:
        df = pd.DataFrame(records)
        st.subheader("Fund Scorecard Metrics")
        st.dataframe(df)
    else:
        st.error("No scorecard metrics found.")
