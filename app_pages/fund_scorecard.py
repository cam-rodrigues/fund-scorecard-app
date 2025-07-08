import streamlit as st
import pandas as pd
import pdfplumber
import io
from difflib import SequenceMatcher
from rapidfuzz import fuzz
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
from tempfile import NamedTemporaryFile

# === Helper Functions ===

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

def find_column_and_row(header_keywords, df):
    for col_idx in range(df.shape[1]):
        for row_idx in range(df.shape[0]):
            cell_value = str(df.iat[row_idx, col_idx])
            if any(keyword.lower() in cell_value.lower() for keyword in header_keywords):
                return col_idx, row_idx + 1  # Start of data row is next row
    return None, None

def apply_statuses_to_excel(excel_file, sheet_name, fund_list, statuses):
    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    df = pd.DataFrame(ws.values)
    invest_col, invest_start_row = find_column_and_row(["Investment Option"], df)
    status_col, status_start_row = find_column_and_row(["Current Period", "Current Quarter", "Current Quarter Status"], df)

    if invest_col is None or status_col is None:
        raise ValueError("Could not find required column headers.")

    fund_status_map = {name: status for name, status in statuses}
    green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for i, user_fund in enumerate(fund_list):
        best_match = None
        best_score = 0
        for extracted_fund in fund_status_map:
            score = fuzz.token_sort_ratio(user_fund.lower(), extracted_fund.lower())
            if score > best_score:
                best_score = score
                best_match = extracted_fund
        row_idx = invest_start_row + i
        cell = ws.cell(row=row_idx + 1, column=status_col + 1)
        cell.fill = PatternFill()  # Clear formatting
        if best_score > 70:
            status = fund_status_map[best_match]
            cell.value = status
            cell.fill = green if status == "Pass" else red
        else:
            cell.value = ""

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
        3. Choose the target worksheet.
        4. Click **Run Matching** to apply statuses.
        5. Download the updated Excel file with color-coded results.
        """)

    uploaded_pdf = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
    uploaded_excel = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    investment_input = st.text_area("Paste Investment Options (one per line)", height=200)

    if uploaded_excel:
        wb = load_workbook(uploaded_excel, read_only=True)
        sheet_names = wb.sheetnames
        selected_sheet = st.selectbox("Select Worksheet", sheet_names)
    else:
        selected_sheet = None

    if st.button("▶ Run Matching"):
        if not uploaded_pdf or not uploaded_excel or not investment_input or not selected_sheet:
            st.error("Please upload all required files, paste your options, and select a sheet.")
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
