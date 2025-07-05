
import streamlit as st
import io
import pdfplumber
import pandas as pd
import base64
import string
import gc
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from rapidfuzz import process, fuzz

# Page config
st.set_page_config(page_title="FidSync", layout="wide")

# Theme colors (Procyon palette)
PRIMARY_COLOR = "#003865"
BG_COLOR = "#FFFFFF"
SECONDARY_BG = "#F5F7FA"
TEXT_COLOR = "#003865"

GREEN_FILL = PatternFill(fill_type="solid", start_color="C6EFCE", end_color="C6EFCE")
RED_FILL = PatternFill(fill_type="solid", start_color="FFC7CE", end_color="FFC7CE")

# Sidebar navigation
with st.sidebar:
    st.markdown("<h1 style='color:#003865;'>FidSync</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Navigate")
    nav_choice = st.radio("Navigation", ["About FidSync", "How to Use"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### Tools")
    tool_choice = st.radio("Available Tools", ["Fund Scorecard"], label_visibility="collapsed")

    st.markdown("---")
    dark_mode = st.checkbox("Dark Mode (WIP)")

# Normalize function
def normalize_name(name):
    name = name.lower().translate(str.maketrans('', '', string.punctuation))
    return " ".join(name.split())

# Extract statuses
def extract_fund_status(pdf_bytes, start_page, end_page):
    fund_status = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num in range(start_page-1, end_page):  # user enters actual page numbers
            if page_num >= len(pdf.pages):
                continue
            text = pdf.pages[page_num].extract_text() or ""
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if "manager tenure" in line.lower() and i > 0:
                    fund_line = lines[i - 1].strip()
                    if "Fund Meets Watchlist Criteria." in fund_line:
                        name = fund_line.split("Fund Meets Watchlist Criteria.")[0].strip()
                        fund_status[normalize_name(name)] = "Pass"
                    elif "Fund has been placed on watchlist" in fund_line:
                        name = fund_line.split("Fund has been placed on watchlist")[0].strip()
                        fund_status[normalize_name(name)] = "Fail"
    return fund_status

# Update Excel logic
def update_excel_with_status(pdf_bytes, excel_bytes, sheet_name, status_col, start_row, fund_names, start_page, end_page, dry_run=False):
    fund_status_map = extract_fund_status(pdf_bytes, start_page, end_page)
    pdf_names = list(fund_status_map.keys())
    wb = load_workbook(io.BytesIO(excel_bytes))
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet '{sheet_name}' not found.")
    ws = wb[sheet_name]

    updated_count = 0
    match_log = []

    for i, fund_name in enumerate(fund_names):
        normalized = normalize_name(fund_name)
        match = process.extractOne(normalized, pdf_names, scorer=fuzz.token_sort_ratio)
        row = start_row + i
        if match and match[1] >= 70:
            matched_name, score = match
            status = fund_status_map.get(matched_name)
            if not dry_run:
                cell = ws[f"{status_col}{row}"]
                if cell.data_type != 'f':
                    cell.value = status
                    cell.fill = GREEN_FILL if status == "Pass" else RED_FILL if status == "Fail" else PatternFill()
                    cell.number_format = 'General'
                    updated_count += 1
            match_log.append((fund_name, matched_name, score, status))
        else:
            match_log.append((fund_name, "No match", 0, "N/A"))

    out_bytes = io.BytesIO()
    wb.save(out_bytes)
    out_bytes.seek(0)
    return out_bytes, updated_count, match_log

# ROUTING: About
if nav_choice == "About FidSync":
    st.header("About FidSync")
    st.markdown("""
    FidSync is your command center for investment-related document processing and analytics.  
    It helps automate manual scorecard reviews and will expand to include compliance checks, plan comparisons, and audit tracking.
    """)

# ROUTING: How to Use
elif nav_choice == "How to Use":
    st.header("How to Use FidSync")
    st.markdown("""
    **To use the Fund Scorecard Tool:**
    1. Upload your PDF fund scorecard and Excel workbook.
    2. Enter the Excel sheet name, starting row and column, and paste your fund names.
    3. Choose the page range where fund statuses are found.
    4. Run the update to see results and download updated files.
    """)

# ROUTING: Fund Scorecard Tool
elif tool_choice == "Fund Scorecard":
    st.header("Fund Scorecard Tool")

    with st.expander("Upload Files"):
        pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Workbook", type=["xlsx", "xlsm"])

    with st.expander("Settings"):
        col1, col2, col3 = st.columns(3)
        sheet_name = col1.text_input("Excel Sheet Name", value="")
        status_col = col2.text_input("Starting Column Letter", value="").strip().upper()
        start_row = col3.number_input("Starting Row Number", min_value=1, value=1)

        col4, col5 = st.columns(2)
        start_page = col4.number_input("Start Page in PDF", min_value=1, value=20)
        end_page = col5.number_input("End Page in PDF", min_value=1, value=30)

        fund_names_input = st.text_area("Investment Option Names (One Per Line)", height=200)
        dry_run = st.checkbox("Dry Run (Preview match only, no Excel changes)", value=False)

    if st.button("Run Status Update"):
        if not pdf_file or not excel_file:
            st.warning("Upload both PDF and Excel files.")
        elif not fund_names_input.strip():
            st.warning("Enter at least one investment option name.")
        else:
            with st.spinner("Processing..."):
                try:
                    fund_names = [line.strip() for line in fund_names_input.strip().splitlines() if line.strip()]
                    pdf_bytes = pdf_file.read()
                    excel_bytes = excel_file.read()

                    updated_excel, count, match_log = update_excel_with_status(
                        pdf_bytes, excel_bytes, sheet_name, status_col,
                        start_row, fund_names, start_page, end_page,
                        dry_run
                    )

                    if dry_run:
                        st.info("Dry run complete. No changes made.")
                    else:
                        st.success(f"Updated {count} row(s).")
                        b64 = base64.b64encode(updated_excel.getvalue()).decode()
                        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Updated_Investment_Status.xlsx">Download Updated Excel</a>'
                        st.markdown(href, unsafe_allow_html=True)

                    st.markdown("### Match Log")
                    df_log = pd.DataFrame(match_log, columns=["Input Name", "Matched Name", "Match Score", "Status"])
                    st.dataframe(df_log)

                    csv_buffer = io.StringIO()
                    df_log.to_csv(csv_buffer, index=False)
                    csv_b64 = base64.b64encode(csv_buffer.getvalue().encode()).decode()
                    log_href = f'<a href="data:file/csv;base64,{csv_b64}" download="match_log.csv">Download Match Log CSV</a>'
                    st.markdown(log_href, unsafe_allow_html=True)

                    del pdf_bytes, excel_bytes, updated_excel, df_log
                    gc.collect()

                except Exception as e:
                    st.error("Something went wrong. Double-check inputs.")
                    st.exception(e)

# Footer
st.sidebar.caption(f"Version 1.2 • Updated {datetime.today().strftime('%b %d, %Y')}")
