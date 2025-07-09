import streamlit as st
import pandas as pd
import pdfplumber
import io
from rapidfuzz import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

# ================================
# PDF Parsing
# ================================
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
                    status_line = line.lower()
                    for offset in range(1, 3):
                        try:
                            possible_status = lines[i - offset].strip()
                            if "Fund Meets Watchlist Criteria" in possible_status:
                                fund_data.append((fund_name, "Pass"))
                                break
                            elif "Fund has been placed on watchlist" in possible_status:
                                fund_data.append((fund_name, "Review"))
                                break
                        except IndexError:
                            continue
    return fund_data

# ================================
# Excel Parsing & Coloring
# ================================
def find_column(df, keyword):
    for col in df.columns:
        if keyword.lower() in str(col).lower():
            return col
    return None

def apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_fund_data):
    wb = load_workbook(filename=excel_file)
    ws = wb[sheet_name]

    df = pd.DataFrame(ws.values)
    headers = df.iloc[0]
    df.columns = headers
    df = df[1:]

    inv_col = find_column(df, "Investment Option")
    stat_col = find_column(df, "Current Period")

    inv_idx = df.columns.get_loc(inv_col) + 1
    stat_idx = df.columns.get_loc(stat_col) + 1

    start_row = 2  # assuming header is row 1

    fund_dict = {name: status for name, status in pdf_fund_data}
    fill_pass = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # green
    fill_review = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # red

    for i, fund in enumerate(investment_options):
        fund = fund.strip()
        best_match, score = process.extractOne(fund, fund_dict.keys(), scorer=fuzz.token_sort_ratio)
        if score > 85:
            status = fund_dict[best_match]
            cell = ws.cell(row=start_row + i, column=stat_idx)
            cell.value = status
            cell.fill = fill_pass if status == "Pass" else fill_review
        else:
            ws.cell(row=start_row + i, column=stat_idx).value = ""

    # Clear old formatting
    for row in ws.iter_rows(min_row=start_row, min_col=stat_idx, max_col=stat_idx):
        for cell in row:
            cell.fill = PatternFill()

    return wb

# ================================
# Streamlit App
# ================================
def run():
    st.title("FidSync: Fund Scorecard Matching")
    st.markdown("""
    This tool compares funds in a PDF Scorecard with Investment Options in Excel and updates status.
    - ✅ **Pass** = Green fill
    - ❌ **Review** = Red fill
    """)

    pdf_file = st.file_uploader("Upload PDF Fund Scorecard", type="pdf")
    excel_file = st.file_uploader("Upload Excel File", type="xlsx")

    investment_input = st.text_area("Paste Investment Options (one per line):")
    investment_options = [line.strip() for line in investment_input.strip().split("\n") if line.strip()]

    if excel_file:
        xls = pd.ExcelFile(excel_file)
        sheet_name = st.selectbox("Choose Excel Sheet", xls.sheet_names)
    else:
        sheet_name = None

    if st.button("Run Matching"):
        if not pdf_file or not excel_file or not investment_options or not sheet_name:
            st.error("Please upload all files and paste investment options before proceeding.")
            return

        st.info("Processing PDF...")
        pdf_data = extract_funds_from_pdf(pdf_file)

        st.success(f"Extracted {len(pdf_data)} funds from PDF")

        st.info("Updating Excel...")
        updated_wb = apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_data)

        output = io.BytesIO()
        updated_wb.save(output)
        st.download_button("📥 Download Updated Excel", output.getvalue(), file_name="Updated_Fund_Scorecard.xlsx")

