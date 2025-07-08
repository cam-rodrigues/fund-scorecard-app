import streamlit as st
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from tempfile import NamedTemporaryFile

# === PDF Parsing ===

def extract_pdf_statuses(pdf_file):
    results = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text or "Fund Scorecard" not in text:
                continue
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "Manager Tenure" in line and i > 0:
                    fund_name = lines[i - 1].strip()
                    for j in range(i, min(i + 5, len(lines))):
                        if "Fund Meets Watchlist Criteria" in lines[j]:
                            results.append((fund_name, "Pass"))
                            break
                        elif "Fund has been placed on watchlist for not meeting" in lines[j]:
                            results.append((fund_name, "Review"))
                            break
    return results

# === Column Detection Helpers ===

def find_column_and_data_start(sheet, column_keywords):
    for row in sheet.iter_rows(min_row=1, max_row=20):
        for cell in row:
            if cell.value and any(k.lower() in str(cell.value).lower() for k in column_keywords):
                col_letter = cell.column
                data_start_row = cell.row + 1
                return col_letter, data_start_row
    return None, None

# === Apply Statuses ===

def apply_statuses_to_excel(excel_file, sheet_name, fund_list, statuses):
    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    # Find columns
    invest_col, invest_row = find_column_and_data_start(ws, ["Investment Option"])
    status_col, status_row = find_column_and_data_start(ws, ["Current Quarter Status", "Current Period"])

    if invest_col is None or status_col is None:
        raise ValueError("Could not find 'Investment Option' or 'Current Quarter Status' columns.")

    # Make sure we're on the same row line
    row_start = max(invest_row, status_row)

    fund_status_map = {name: status for name, status in statuses}
    green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for i, user_fund in enumerate(fund_list):
        row_idx = row_start + i
        fund_cell = ws.cell(row=row_idx, column=invest_col)
        status_cell = ws.cell(row=row_idx, column=status_col)

        # Clear existing value + formatting
        status_cell.value = None
        status_cell.fill = PatternFill()

        best_match = None
        best_score = 0
        for extracted_fund in fund_status_map:
            score = fuzz.token_sort_ratio(user_fund.lower(), extracted_fund.lower())
            if score > best_score:
                best_score = score
                best_match = extracted_fund

        if best_score > 70:
            result = fund_status_map[best_match]
            status_cell.value = result
            status_cell.fill = green if result == "Pass" else red
        else:
            status_cell.value = ""

    temp_file = NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(temp_file.name)
    return temp_file.name

# === Streamlit App ===

def run():
    st.set_page_config(layout="wide")
    st.title("📊 FidSync: Fund Scorecard Matching")

    with st.expander("📌 Instructions"):
        st.markdown("""
        1. Upload a **PDF Fund Scorecard** and an **Excel workbook (.xlsx)**.
        2. Paste your **Investment Options** (in the correct order, one per line).
        3. Choose the worksheet that contains your data.
        4. Click **Run Matching** to apply statuses.
        5. Download the updated file with red/green cell statuses under **Current Quarter Status**.
        """)

    uploaded_pdf = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
    uploaded_excel = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    investment_input = st.text_area("Paste Investment Options (one per line)", height=200)

    selected_sheet = None
    if uploaded_excel:
        wb = load_workbook(uploaded_excel, read_only=True)
        selected_sheet = st.selectbox("Select Worksheet", wb.sheetnames)

    if st.button("▶ Run Matching"):
        if not uploaded_pdf or not uploaded_excel or not investment_input or not selected_sheet:
            st.error("Please upload all required files, paste options, and select a worksheet.")
            return

        try:
            investment_options = [line.strip() for line in investment_input.splitlines() if line.strip()]
            statuses = extract_pdf_statuses(uploaded_pdf)
            updated_file_path = apply_statuses_to_excel(uploaded_excel, selected_sheet, investment_options, statuses)
            with open(updated_file_path, "rb") as f:
                st.success("✅ Matching complete!")
                st.download_button("📥 Download Updated Excel", f, file_name="Updated_Scorecard.xlsx")
        except Exception as e:
            st.error(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
