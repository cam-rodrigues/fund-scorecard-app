import streamlit as st
import pandas as pd
import pdfplumber
import io
from difflib import SequenceMatcher
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from tempfile import NamedTemporaryFile
import os

# ---------- PDF Parsing Logic ----------
def extract_fund_data_from_pdf(pdf_file):
    fund_data = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text or "Fund Scorecard" not in text:
                continue
            if "Criteria Threshold" in text:
                continue

            lines = text.splitlines()
            for idx, line in enumerate(lines):
                if "Manager Tenure" in line and idx > 0:
                    fund_name = lines[idx - 1].strip()

                    if "Fund Meets Watchlist Criteria" in line:
                        status = "Pass"
                    elif "Fund has been placed on watchlist" in line:
                        status = "Review"
                    else:
                        continue

                    fund_data.append((fund_name, status))

    return fund_data

# ---------- Fuzzy Matching ----------
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fuzzy_match(fund_name, options, threshold=0.7):
    best_match = None
    best_score = 0
    for option in options:
        score = similar(fund_name, option)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = option
    return best_match

# ---------- Excel Processing ----------
def find_column(df, keyword):
    for col in df.columns:
        for idx, val in enumerate(df[col]):
            if isinstance(val, str) and keyword.lower() in val.lower():
                return col, idx + 1  # Return column and row after header
    return None, None

def update_excel(excel_file, sheet_name, fund_data, investment_list):
    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)

    inv_col, inv_start_row = find_column(df, "Investment Option")
    stat_col, stat_start_row = find_column(df, "Current Quarter Status")

    if inv_col is None or stat_col is None:
        st.error("Could not find 'Investment Option' or 'Current Quarter Status' headers.")
        return None

    inv_col_idx = df.columns.get_loc(inv_col) + 1
    stat_col_idx = df.columns.get_loc(stat_col) + 1

    for i in range(stat_start_row + 1, stat_start_row + 1 + len(investment_list)):
        ws.cell(row=i, column=stat_col_idx).fill = PatternFill(fill_type=None)

    fund_map = {fuzzy_match(fund, investment_list): status for fund, status in fund_data}

    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for i, investment in enumerate(investment_list):
        row = stat_start_row + 1 + i
        status = fund_map.get(investment)
        cell = ws.cell(row=row, column=stat_col_idx)

        if status == "Pass":
            cell.value = "Pass"
            cell.fill = green_fill
        elif status == "Review":
            cell.value = "Review"
            cell.fill = red_fill
        else:
            cell.value = None
            cell.fill = PatternFill(fill_type=None)

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        wb.save(tmp.name)
        return tmp.name

# ---------- Main Streamlit UI ----------
def run():
    st.title("📊 FidSync: Fund Scorecard Matching")

    st.markdown("""
    Extract fund statuses from your PDF, match them to your Excel, and generate a color-coded scorecard.
    """)

    pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
    excel_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    investment_input = st.text_area("Paste Investment Options (one per line, same order as Excel)", height=200)

    if pdf_file and excel_file and investment_input:
        try:
            investment_list = [line.strip() for line in investment_input.splitlines() if line.strip()]
            fund_data = extract_fund_data_from_pdf(pdf_file)

            with st.expander("🔍 Preview Extracted Fund Data from PDF"):
                st.dataframe(pd.DataFrame(fund_data, columns=["Fund Name", "Status"]))

            xls = pd.ExcelFile(excel_file)
            sheet_name = st.selectbox("Select Worksheet", xls.sheet_names)

            if st.button("Run Matching & Update Excel"):
                updated_path = update_excel(excel_file, sheet_name, fund_data, investment_list)

                if updated_path:
                    with open(updated_path, "rb") as f:
                        st.success("✅ Excel file updated successfully!")
                        st.download_button("📥 Download Updated Excel", data=f, file_name="updated_fund_scorecard.xlsx")
                    os.remove(updated_path)

        except Exception as e:
            st.error(f"❌ Error: {e}")

    else:
        st.info("⬆️ Upload both files and paste investment options to get started.")
