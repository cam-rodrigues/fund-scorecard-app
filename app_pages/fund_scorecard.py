import streamlit as st
import pandas as pd
import pdfplumber
from difflib import SequenceMatcher
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from tempfile import NamedTemporaryFile
import os

# ---------- PDF Parsing ----------
def extract_funds_from_pdf(pdf_file):
    fund_data = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text or "Fund Scorecard" not in text:
                continue
            if "Criteria Threshold" in text:
                continue

            lines = text.splitlines()
            for i, line in enumerate(lines):
                if "Fund Meets Watchlist Criteria" in line and i > 0:
                    candidate = lines[i - 1].strip()
                    if is_valid_fund_name(candidate):
                        fund_data.append((candidate, "Pass"))
                elif "Fund has been placed on watchlist" in line and i > 0:
                    candidate = lines[i - 1].strip()
                    if is_valid_fund_name(candidate):
                        fund_data.append((candidate, "Review"))

    return fund_data

def is_valid_fund_name(name):
    if not name or len(name) < 5:
        return False
    blacklist = ["Investment Options", "Tracking Error", "Rank", "The fund", "Review"]
    return not any(bad in name for bad in blacklist)

# ---------- Fuzzy Matching ----------
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fuzzy_match(name, options, threshold=0.7):
    best = None
    best_score = 0
    for opt in options:
        score = similar(name, opt)
        if score > best_score and score >= threshold:
            best = opt
            best_score = score
    return best

# ---------- Excel Handling ----------
def find_column(df, keyword):
    for col in df.columns:
        for i, val in enumerate(df[col]):
            if isinstance(val, str) and keyword.lower() in val.lower():
                return col, i + 1
    return None, None

def update_excel(file, sheet, fund_data, investment_list):
    wb = load_workbook(file)
    ws = wb[sheet]
    df = pd.read_excel(file, sheet_name=sheet, dtype=str)

    inv_col, inv_start = find_column(df, "Investment Option")
    stat_col, stat_start = find_column(df, "Current Quarter Status")

    if not inv_col or not stat_col:
        st.error("Headers 'Investment Option' or 'Current Quarter Status' not found.")
        return None

    inv_col_idx = df.columns.get_loc(inv_col) + 1
    stat_col_idx = df.columns.get_loc(stat_col) + 1

    # Clear formatting in target column
    for i in range(stat_start + 1, stat_start + 1 + len(investment_list)):
        ws.cell(row=i, column=stat_col_idx).fill = PatternFill(fill_type=None)

    green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    pdf_status_map = {fuzzy_match(name, investment_list): status for name, status in fund_data}

    for i, inv in enumerate(investment_list):
        row = stat_start + 1 + i
        status = pdf_status_map.get(inv)
        cell = ws.cell(row=row, column=stat_col_idx)
        if status == "Pass":
            cell.value = "Pass"
            cell.fill = green
        elif status == "Review":
            cell.value = "Review"
            cell.fill = red
        else:
            cell.value = None
            cell.fill = PatternFill(fill_type=None)

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        wb.save(tmp.name)
        return tmp.name

# ---------- Streamlit App ----------
def run():
    st.title("📊 FidSync: Fund Scorecard Matching")

    st.markdown("""
    Match PDF fund watchlist results to your Excel investment options. Color-coded and clean.
    """)

    pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
    excel_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    investment_input = st.text_area("Paste Investment Option Names (one per line)", height=200)

    if pdf_file and excel_file and investment_input:
        try:
            investment_list = [line.strip() for line in investment_input.splitlines() if line.strip()]
            fund_data = extract_funds_from_pdf(pdf_file)

            st.write("✅ Extracted Fund Entries from PDF")
            st.dataframe(pd.DataFrame(fund_data, columns=["Fund Name", "Status"]))

            xls = pd.ExcelFile(excel_file)
            sheet = st.selectbox("Choose Worksheet", xls.sheet_names)

            if st.button("🔁 Match and Update Excel"):
                updated_file = update_excel(excel_file, sheet, fund_data, investment_list)

                if updated_file:
                    with open(updated_file, "rb") as f:
                        st.success("✅ Excel updated successfully!")
                        st.download_button("📥 Download Updated File", data=f, file_name="updated_scorecard.xlsx")
                    os.remove(updated_file)

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
    else:
        st.info("⬆️ Upload both files and paste investment options to get started.")
