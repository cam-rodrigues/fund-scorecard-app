
import streamlit as st
import io
import base64
import pandas as pd
import pdfplumber
import string
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from rapidfuzz import process, fuzz

# === PAGE SETUP ===
st.set_page_config(page_title="FidSync", layout="wide")

# === STATE INITIALIZATION ===
if "view" not in st.session_state:
    st.session_state.view = "About FidSync"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# === SIDEBAR ===
with st.sidebar:
    st.title("FidSync")
    st.markdown("---")
    st.markdown("**Navigate**")
    nav_options = ["About FidSync", "How to Use", "Fund Scorecard"]
    view = st.radio("Select a view", nav_options, index=nav_options.index(st.session_state.view), label_visibility="collapsed")
    st.session_state.view = view

    st.markdown("---")
    st.checkbox("Dark Mode", key="dark_mode")

# === UTILS ===
def normalize_name(name: str) -> str:
    name = name.lower().translate(str.maketrans('', '', string.punctuation))
    return " ".join(name.split())

GREEN_FILL = PatternFill(fill_type="solid", start_color="C6EFCE", end_color="C6EFCE")
RED_FILL = PatternFill(fill_type="solid", start_color="FFC7CE", end_color="FFC7CE")

def extract_fund_status(pdf_bytes, start_page, end_page):
    fund_status = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num in range(start_page - 1, end_page):
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

def update_excel_with_status(pdf_bytes, excel_bytes, sheet_name, status_col, start_row, fund_names, start_page, end_page):
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

# === MAIN VIEW LOGIC ===
if st.session_state.view == "About FidSync":
    st.header("About FidSync")
    st.markdown("""
FidSync is a secure and intelligent investment operations platform designed to help plan advisors and investment teams efficiently manage fund oversight, compliance, and reporting.

**Current Capabilities:**
- Extract statuses from PDF scorecards
- Update fund statuses in Excel based on fuzzy matches

**Planned Features:**
- Compliance check automation
- Plan-to-plan comparisons
- Centralized audit logs and history

""")

elif st.session_state.view == "How to Use":
    st.header("How to Use FidSync")
    st.markdown("""
1. **Prepare Your Files**  
   Upload a fund scorecard PDF and an Excel workbook with investment names listed vertically.

2. **Enter Configuration Settings**  
   Specify the sheet name, starting column, and row number. Also enter the actual page numbers in the PDF where scorecards appear.

3. **Paste Fund Names**  
   Provide investment option names, one per line, in the textbox.

4. **Run the Tool**  
   Press **Run Status Update** to apply updates to your Excel file. You can also choose **Dry Run** to preview matches without modifying the file.

5. **Download Results**  
   After the tool completes, download both the updated Excel workbook and a CSV match log.
""")

elif st.session_state.view == "Fund Scorecard":
    st.header("Fund Scorecard Status Tool")

    with st.form("upload_form"):
        st.subheader("Upload Files")
        pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Workbook", type=["xlsx", "xlsm"])

        st.subheader("Settings")
        col1, col2, col3 = st.columns(3)
        sheet_name = col1.text_input("Excel Sheet Name")
        status_col = col2.text_input("Starting Column Letter").strip().upper()
        start_row = col3.number_input("Starting Row Number", min_value=1)

        col4, col5 = st.columns(2)
        start_page = col4.number_input("Start Page in PDF (actual page #)", min_value=1)
        end_page = col5.number_input("End Page in PDF (actual page #)", min_value=1)

        fund_names_input = st.text_area("Investment Option Names (One Per Line)", height=200)
        dry_run = st.checkbox("Dry Run (Preview Only)", value=False)

        submitted = st.form_submit_button("Run Status Update")

    if submitted:
        if not pdf_file or not excel_file:
            st.warning("Please upload both PDF and Excel files.")
        elif start_page > end_page:
            st.error("Start Page must be less than or equal to End Page.")
        elif not fund_names_input.strip():
            st.warning("Please enter investment option names.")
        else:
            with st.spinner("Processing..."):
                try:
                    fund_names = [line.strip() for line in fund_names_input.strip().splitlines() if line.strip()]
                    pdf_bytes = pdf_file.read()
                    excel_bytes = excel_file.read()

                    updated_excel, count, match_log = update_excel_with_status(
                        pdf_bytes, excel_bytes, sheet_name, status_col,
                        start_row, fund_names, start_page, end_page
                    )

                    if dry_run:
                        st.info("Dry run complete. No changes made to Excel.")
                    else:
                        st.success(f"Successfully updated {count} row(s).")

                        b64 = base64.b64encode(updated_excel.getvalue()).decode()
                        link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Updated_Investment_Status.xlsx">Download Updated Excel</a>'
                        st.markdown(link, unsafe_allow_html=True)

                    # Match Log Table
                    st.markdown("### Match Log")
                    df_log = pd.DataFrame(match_log, columns=["Input Name", "Matched Name", "Match Score", "Status"])
                    st.dataframe(df_log)

                    # CSV Log Download
                    csv_buffer = io.StringIO()
                    df_log.to_csv(csv_buffer, index=False)
                    csv_b64 = base64.b64encode(csv_buffer.getvalue().encode()).decode()
                    csv_link = f'<a href="data:file/csv;base64,{csv_b64}" download="match_log.csv">Download Match Log CSV</a>'
                    st.markdown(csv_link, unsafe_allow_html=True)

                except Exception as e:
                    st.error("An error occurred during processing.")
                    st.exception(e)

