import streamlit as st
import pandas as pd
import pdfplumber
import io
from rapidfuzz import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string

# ===========================
# Extract fund/status from PDF
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
# Excel Status Application w/ Match Preview
# ===========================
def apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_fund_data, status_cell):
    col_letter = ''.join(filter(str.isalpha, status_cell))
    row_number = int(''.join(filter(str.isdigit, status_cell)))
    col_index = column_index_from_string(col_letter)
    start_row = row_number + 1

    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    fund_dict = {}
    for item in pdf_fund_data:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            name, status = item
            fund_dict[name.strip()] = status.strip()

    fill_pass = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fill_review = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for row in ws.iter_rows(min_row=start_row, min_col=col_index, max_col=col_index, max_row=start_row + len(investment_options)):
        for cell in row:
            cell.fill = PatternFill()

    results = []

    for i, fund in enumerate(investment_options):
        fund = fund.strip()
        best_match, score = process.extractOne(fund, fund_dict.keys(), scorer=fuzz.token_sort_ratio)
        matched_status = None

        cell = ws.cell(row=start_row + i, column=col_index)
        if best_match and score >= 85:
            matched_status = fund_dict[best_match]
            cell.value = matched_status
            cell.fill = fill_pass if matched_status == "Pass" else fill_review
        else:
            cell.value = ""

        results.append({
            "Your Input": fund,
            "Matched Fund Name": best_match or "",
            "Status": matched_status or "",
            "Match Score": round(score or 0, 1)
        })

    st.subheader("🔍 Match Preview")
    st.dataframe(pd.DataFrame(results))

    return wb

# ===========================
# Streamlit App
# ===========================
def run():
    st.title("📊 FidSync: Fund Scorecard Matching")
    st.markdown("""
    Match fund data from a PDF Scorecard to your Excel investment option sheet.

    **Steps:**
    1. Upload your PDF Scorecard and Excel file
    2. Paste your investment options (in Excel order)
    3. Enter the cell where 'Current Quarter Status' appears (e.g. `L6`)
    4. Click Run and preview the matches before downloading
    """)

    pdf_file = st.file_uploader("Upload PDF Fund Scorecard", type="pdf")
    excel_file = st.file_uploader("Upload Excel File", type="xlsx")

    investment_input = st.text_area("Paste Investment Options (one per line):")
    investment_options = [line.strip() for line in investment_input.strip().split("\n") if line.strip()]

    status_cell = st.text_input("Enter the cell where 'Current Quarter Status' appears (e.g., L6):")

    sheet_name = None
    if excel_file:
        try:
            xls = pd.ExcelFile(excel_file)
            sheet_name = st.selectbox("Choose Excel Sheet", xls.sheet_names)
        except Exception as e:
            st.error(f"❌ Could not read Excel: {e}")
            return

    if st.button("Run Matching"):
        if not pdf_file or not excel_file or not investment_options or not sheet_name or not status_cell:
            st.error("Please upload all files and enter the 'Current Quarter Status' cell.")
            return

        st.info("Extracting from PDF...")
        pdf_data = extract_funds_from_pdf(pdf_file)
        st.success(f"✅ Extracted {len(pdf_data)} fund entries from PDF")

        try:
            st.info("Matching and updating Excel...")
            updated_wb = apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_data, status_cell)

            output = io.BytesIO()
            updated_wb.save(output)
            st.download_button("📥 Download Updated Excel", output.getvalue(), file_name="Updated_Fund_Scorecard.xlsx")

        except Exception as e:
            st.error(f"❌ Failed to update Excel: {e}")
