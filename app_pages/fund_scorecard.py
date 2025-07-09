import streamlit as st
import pandas as pd
import pdfplumber
import io
from rapidfuzz import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# ===========================
# PDF Extraction (Safe)
# ===========================
def extract_funds_from_pdf(pdf_file):
    fund_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if "Fund Scorecard" not in text or "Criteria Threshold" in text:
                continue
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "Manager Tenure" in line and i > 0:
                    fund_name = lines[i - 1].strip()
                    status = None
                    for offset in range(1, 4):
                        try:
                            check_line = lines[i - offset].strip()
                            if "Fund Meets Watchlist Criteria" in check_line:
                                status = "Pass"
                                break
                            elif "Fund has been placed on watchlist" in check_line:
                                status = "Review"
                                break
                        except IndexError:
                            continue
                    if fund_name and status:
                        fund_data.append((str(fund_name).strip(), str(status).strip()))
    return fund_data

# ===========================
# Excel Helpers
# ===========================
def find_correct_header_row(df, target_columns):
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        row_vals = [str(cell).strip().lower() for cell in row if pd.notna(cell)]
        if all(any(tc.lower() in val for val in row_vals) for tc in target_columns):
            return i
    return 0

def find_column(df, keyword):
    best_match = None
    best_score = 0
    for col in df.columns:
        if col is None or pd.isna(col):
            continue
        score = fuzz.partial_ratio(str(col).lower(), keyword.lower())
        if score > best_score and score >= 70:
            best_match = col
            best_score = score
    return best_match

# ===========================
# Excel Processing Logic
# ===========================
def apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_fund_data):
    df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    header_row = find_correct_header_row(df_raw, ["Investment Option", "Current Quarter Status"])
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
    st.write("📄 Excel Headers Detected:", list(df.columns))

    inv_col = find_column(df, "Investment Option")
    stat_col = find_column(df, "Current Quarter Status")
    if not inv_col or not stat_col:
        raise ValueError("Missing required columns.")

    inv_idx = df.columns.get_loc(inv_col) + 1
    stat_idx = df.columns.get_loc(stat_col) + 1
    start_row = header_row + 2

    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    # ✅ Safe fund dictionary
    fund_dict = {}
    for item in pdf_fund_data:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            name, status = item
            fund_dict[name.strip()] = status.strip()

    fill_pass = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fill_review = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for row in ws.iter_rows(min_row=start_row, min_col=stat_idx, max_col=stat_idx, max_row=start_row + len(investment_options)):
        for cell in row:
            cell.fill = PatternFill()

    for i, fund in enumerate(investment_options):
        fund = fund.strip()
        best_match, score = process.extractOne(fund, fund_dict.keys(), scorer=fuzz.token_sort_ratio)
        cell = ws.cell(row=start_row + i, column=stat_idx)
        if score >= 85:
            status = fund_dict[best_match]
            cell.value = status
            cell.fill = fill_pass if status == "Pass" else fill_review
        else:
            cell.value = ""

    return wb

# ===========================
# Streamlit UI
# ===========================
def run():
    st.title("📊 FidSync: Fund Scorecard Matching")
    st.markdown("""
    Upload your fund scorecard PDF and Excel template. This tool matches funds and updates the Excel with color-coded statuses.
    - ✅ Green = **Pass**
    - ❌ Red = **Review**
    """)

    pdf_file = st.file_uploader("Upload PDF Fund Scorecard", type="pdf")
    excel_file = st.file_uploader("Upload Excel File", type="xlsx")

    investment_input = st.text_area("Paste Investment Options (one per line):")
    investment_options = [line.strip() for line in investment_input.strip().split("\n") if line.strip()]

    sheet_name = None
    if excel_file:
        try:
            xls = pd.ExcelFile(excel_file)
            sheet_name = st.selectbox("Choose Excel Sheet", xls.sheet_names)
        except Exception as e:
            st.error(f"❌ Could not read Excel: {e}")
            return

    if st.button("Run Matching"):
        if not pdf_file or not excel_file or not investment_options or not sheet_name:
            st.error("Please upload all files and paste investment options before proceeding.")
            return

        st.info("Extracting from PDF...")
        pdf_data = extract_funds_from_pdf(pdf_file)
        st.success(f"✅ Extracted {len(pdf_data)} fund statuses from PDF")

        try:
            st.info("Updating Excel...")
            updated_wb = apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_data)

            output = io.BytesIO()
            updated_wb.save(output)
            st.download_button("📥 Download Updated Excel", output.getvalue(), file_name="Updated_Fund_Scorecard.xlsx")
        except Exception as e:
            st.error(f"❌ Excel update failed: {e}")
