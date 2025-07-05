
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

# === Page Config ===
st.set_page_config(page_title="FidSync", layout="wide")

# === Custom Sidebar Navigation ===
st.sidebar.title("FidSync")
st.sidebar.markdown("###### Your investment operations assistant.")
st.sidebar.markdown("---")
navigation = st.sidebar.radio("**Navigate**", ["About FidSync", "How to Use"])
st.sidebar.markdown("---")
st.sidebar.markdown("#### Tools")
tool_selected = st.sidebar.radio("", ["Fund Scorecard"])
st.sidebar.markdown("---")
dark_mode = st.sidebar.toggle("Dark Mode", value=False)

# === Styles for Excel ===
GREEN_FILL = PatternFill(fill_type="solid", start_color="C6EFCE", end_color="C6EFCE")
RED_FILL = PatternFill(fill_type="solid", start_color="FFC7CE", end_color="FFC7CE")

# === Utility Functions ===
def normalize_name(name):
    name = name.lower().translate(str.maketrans('', '', string.punctuation))
    return " ".join(name.split())

def extract_fund_status(pdf_bytes, start_page, end_page):
    fund_status = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num in range(start_page - 1, end_page):  # Adjusted to real page numbers
            if page_num >= len(pdf.pages):
                continue
            lines = (pdf.pages[page_num].extract_text() or "").split('\n')
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
                cell = ws[f"{status_col.upper()}{row}"]
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

# === ROUTING ===
if navigation == "About FidSync":
    st.title("About FidSync")
    st.markdown("""
    **FidSync** is your centralized assistant for investment fund oversight.

    - ✅ Scorecard parsing
    - ✅ Excel status updating
    - 🛡️ Compliance checks (coming soon)
    - 🧮 Plan comparisons (coming soon)
    - 📜 Audit logs (coming soon)

    Built for fund analysts and compliance teams.
    """)

elif navigation == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
    1. Upload the Fund Scorecard PDF.
    2. Upload the Excel workbook that contains fund names.
    3. Enter the sheet name, starting column, row, and page range.
    4. Paste in the list of fund names (one per line).
    5. Click **Run Status Update** to apply the results.

    You can also use **Dry Run** to preview matches without modifying Excel.
    """)

elif tool_selected == "Fund Scorecard":
    st.title("Fund Scorecard Status Tool")

    with st.expander("📂 Upload Files", expanded=True):
        pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Workbook", type=["xlsx", "xlsm"])

    with st.expander("⚙️ Settings", expanded=True):
        col1, col2, col3 = st.columns(3)
        sheet_name = col1.text_input("Excel Sheet Name")
        status_col = col2.text_input("Starting Column Letter")
        start_row = col3.number_input("Starting Row Number", min_value=1)

        col4, col5 = st.columns(2)
        start_page = col4.number_input("Start Page (as shown in PDF)", min_value=1)
        end_page = col5.number_input("End Page (as shown in PDF)", min_value=1)

        fund_names_input = st.text_area("Investment Option Names (One Per Line)", height=200)
        dry_run = st.checkbox("Dry Run (Preview only, don't modify Excel)")

    if st.button("Run Status Update"):
        if not pdf_file or not excel_file:
            st.warning("Please upload both PDF and Excel files.")
        elif start_page > end_page:
            st.error("Start Page must be less than or equal to End Page.")
        elif not fund_names_input.strip():
            st.warning("Investment option names are required.")
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
                    st.success(f"Successfully updated {count} row(s).")
                    st.markdown("### Match Summary")
                    st.dataframe(pd.DataFrame(match_log, columns=["Input", "Matched", "Score", "Status"]))

                    if not dry_run:
                        b64 = base64.b64encode(updated_excel.getvalue()).decode()
                        link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Updated_Fund_Status.xlsx">Download Updated Excel</a>'
                        st.markdown(link, unsafe_allow_html=True)

                except Exception as e:
                    st.error("Something went wrong. Check your inputs.")
                    st.exception(e)

# === Footer ===
st.markdown("<hr style='border:1px solid #e6e6e6'>", unsafe_allow_html=True)
st.caption(f"© 2025 FidSync • Version 1.2 • Updated {datetime.today().strftime('%b %d, %Y')}")
