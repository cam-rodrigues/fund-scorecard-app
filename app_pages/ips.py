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

    # Open PDF once to grab page 1 and 2
    with pdfplumber.open(uploaded_mpi) as pdf:
        # === Step 1: Header Info (Page 1) ===
        first_text = pdf.pages[0].extract_text() or ""
        # Quarter/Year
        date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_text)
        quarter_map = {"3/31": "Q1", "6/30": "Q2", "9/30": "Q3", "12/31": "Q4"}
        if date_match:
            d = date_match.group(1)
            q = quarter_map.get("/".join(d.split("/")[:2]), "Unknown")
            year = d.split("/")[-1]
            st.write(f"**Report Quarter:** {q} {year}")
        else:
            st.error("Could not determine report quarter.")

        # Total Options
        opts = re.search(r"Total Options\s*:\s*(\d+)", first_text)
        st.write(f"**Total Investment Options:** {int(opts.group(1)) if opts else 'N/A'}")

        # Prepared For
        pf = re.search(r"Prepared For\s*:\s*\n(.+)", first_text)
        st.write(f"**Prepared For:** {pf.group(1).strip() if pf else 'N/A'}")

        # Prepared By
        pb = re.search(r"Prepared By\s*:\s*\n(.+)", first_text)
        st.write(f"**Prepared By:** {pb.group(1).strip() if pb else 'N/A'}")

        # === Step 2: Table of Contents (Page 2) ===
        toc_text = pdf.pages[1].extract_text() or ""

    # Show TOC lines for debugging (optional)
    with st.expander("TOC Lines (debug)", expanded=False):
        for line in toc_text.splitlines():
            st.write(line)

    # Locate section start pages
    sections = {"Fund Performance": None, "Fund Scorecard": None}
    for line in toc_text.splitlines():
        low = line.lower()
        if "current vs." in low and "comparison" in low:
            m = re.search(r"(\d+)$", line.strip())
            if m:
                sections["Fund Performance"] = int(m.group(1))
        if "fund scorecard" in low:
            m = re.search(r"(\d+)$", line.strip())
            if m:
                sections["Fund Scorecard"] = int(m.group(1))

    if sections["Fund Performance"]:
        st.write(f"**Fund Performance** → page {sections['Fund Performance']}")
    else:
        st.error("Could not find 'Fund Performance' in TOC.")

    if not sections["Fund Scorecard"]:
        st.error("Could not find 'Fund Scorecard' in TOC.")
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
            # stop when section ends (no “Pass”/“Review” and not scorecard header)
            if i > start_page and "fund scorecard" not in text.lower() and not re.search(r"\b(Pass|Review)\b", text):
                break
            for line in text.splitlines():
                if any(key in line for key in skip_keys):
                    continue
                # Metric line
                m = re.match(r"\s*(.+?)\s+(Pass|Review)\s*(?:[-–—:]\s*(.*))?$", line)
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
                else:
                    # New fund heading
                    if line.strip() and not line.startswith(" "):
                        current_fund = line.strip()

    # === Step 4: Display each fund’s metrics separately ===
    if records:
        df_all = pd.DataFrame(records)
        for fund in df_all['Fund Name'].unique():
            fund_df = df_all[df_all['Fund Name'] == fund][['Metric', 'Status', 'Reason']].copy()
            # Map status to icons
            fund_df['Status'] = fund_df['Status'].map({'Pass': '✅', 'Review': '❌'})
            with st.expander(f"{fund} Scorecard Metrics", expanded=False):
                st.table(fund_df)
    else:
        st.error("No scorecard metrics found.")
