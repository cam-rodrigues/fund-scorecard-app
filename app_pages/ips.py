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

    # Open PDF once for pages 1 & 2
    with pdfplumber.open(uploaded_mpi) as pdf:
        first_text = pdf.pages[0].extract_text() or ""
        toc_text   = pdf.pages[1].extract_text() or ""

    # === Step 1: Header Info (Page 1) ===
    date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_text)
    quarter_map = {"3/31":"Q1","6/30":"Q2","9/30":"Q3","12/31":"Q4"}
    if date_match:
        d = date_match.group(1)
        q = quarter_map.get("/".join(d.split("/")[:2]), "Unknown")
        y = d.split("/")[-1]
        st.write(f"**Report Quarter:** {q} {y}")
    else:
        st.error("Could not determine report quarter.")

    opts = re.search(r"Total Options\s*:\s*(\d+)", first_text)
    st.write(f"**Total Investment Options:** {int(opts.group(1)) if opts else 'N/A'}")

    pf = re.search(r"Prepared For\s*:\s*\n(.+)", first_text)
    st.write(f"**Prepared For:** {pf.group(1).strip() if pf else 'N/A'}")

    pb = re.search(r"Prepared By\s*:\s*\n(.+)", first_text)
    st.write(f"**Prepared By:** {pb.group(1).strip() if pb else 'N/A'}")

    # === Step 2: Parse TOC for key sections (Page 2) ===
    sections = {"Fund Performance": None, "Fund Scorecard": None}
    for raw in toc_text.splitlines():
        line = raw.strip()
        # look for our two sections with optional dots/leader & trailing page number
        for key in sections:
            if key.lower() in line.lower():
                m = re.search(rf"{re.escape(key)}\s*\.{0,}\s*(\d+)$", line)
                if not m:
                    # fallback: any digits at end
                    m = re.search(r"(\d+)$", line)
                if m:
                    sections[key] = int(m.group(1))

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
    skip = ["Fund Scorecard", "Investment Options", "Criteria Threshold"]

    with pdfplumber.open(uploaded_mpi) as pdf:
        for i in range(start_page, len(pdf.pages)):
            text = pdf.pages[i].extract_text() or ""
            # stop once we leave the scorecard section
            if i > start_page and "fund scorecard" not in text.lower() and not re.search(r"\bPass\b|\bReview\b", text):
                break
            for line in text.splitlines():
                if any(s in line for s in skip):
                    continue
                # metric line?
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
                    # new fund heading
                    if line.strip() and not line.startswith(" "):
                        current_fund = line.strip()

    # === Step 4: Display per-fund tables with icons ===
    if not records:
        st.error("No scorecard metrics found.")
        return

    df_all = pd.DataFrame(records)
    for fund in df_all['Fund Name'].unique():
        fund_df = df_all[df_all['Fund Name'] == fund][['Metric','Status','Reason']].copy()
        fund_df['Status'] = fund_df['Status'].map({'Pass':'✅','Review':'❌'})
        with st.expander(f"{fund} Scorecard Metrics", expanded=False):
            st.table(fund_df)
