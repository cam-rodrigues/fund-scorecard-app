# Step 1: Extract Header Information from First Page
import re
import streamlit as st
import pdfplumber

# Assume `uploaded_mpi` is the file-like object from Step 0
with pdfplumber.open(uploaded_mpi) as pdf:
    first_page_text = pdf.pages[0].extract_text() or ""

# 1) Determine the quarter based on the date at top-left
#    Dates are in the form M/D/20YY
date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_page_text)
quarter_map = {
    "3/31":  "Q1",
    "6/30":  "Q2",
    "9/30":  "Q3",
    "12/31": "Q4",
}
if date_match:
    full_date = date_match.group(1)             # e.g. "3/31/2025"
    month_day = full_date.rsplit("/", 1)[0]      # e.g. "3/31"
    quarter = quarter_map.get(month_day, "Unknown Quarter")
    report_year = full_date.split("/")[-1]       # e.g. "2025"
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
