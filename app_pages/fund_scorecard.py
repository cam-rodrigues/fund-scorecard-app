import streamlit as st
import pandas as pd
import pdfplumber
import io
from rapidfuzz import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# =====================================
# Robust PDF Parsing
# =====================================
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
                    nearby_lines = lines[max(0, i - 5): i + 2]
                    for l in nearby_lines:
                        if "Fund Meets Watchlist Criteria" in l:
                            status = "Pass"
                            break
                        elif "Fund has been placed on watchlist" in l:
                            status = "Review"
                            break
                    if fund_name and status:
                        try:
                            fund_data.append((str(fund_name).strip(), str(status).strip()))
                        except Exception as e:
                            st.warning(f"⚠️ Skipped invalid PDF line: {fund_name} / {status} ({e})")
    return fund_data

# =====================================
# Excel Matching & Coloring
# =====================================
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

def apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_fund_data):
    wb = load_workbook(filename=excel_file)
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))

    # Auto-detect header row
    header_row_idx = None
    for i, row in enumerate(rows):
        row_vals = [str(cell).strip().lower() if cell else "" for cell in row]
        if any("investment option" in val for val in row_vals) and any("current quarter status" in val for val in row_vals):
            header_row_idx = i
            break

    if header_row_idx is None:
        raise ValueError("Could not find header row with 'Investment Option' and 'Current Quarter Status'.")

    headers = rows[header_row_idx]
    data = rows[header_row_idx + 1:]
    df = pd.DataFrame(data, columns=headers)
    st.write("📄 Actual Headers Detected:", list(df.columns))

    inv_col = find_column(df, "Investment Option")
    stat_col = find_column(df, "Current Quarter Status")

    if not inv_col or not stat_col:
        raise ValueError("Could not find 'Investment Option' or 'Current Quarter Status' columns in Excel.")

    inv_idx = list(df.columns).index(inv_col) + 1
    stat_idx = list(df.columns).index(stat_col) + 1
    start_row = header_row_idx + 2

    # ✅ Safely build fund dict
    fund_dict = {}
    for item in pdf_fund_data:
        if isinstance(item, tuple) and len(item) == 2 and all(item):
            name, status = item
            fund_dict[name] = status
        else:
            st.warning(f"⚠️ Skipped malformed PDF entry: {item}")

    fill_pass = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fill_review = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    # Clear formatting
    for row in ws.iter_rows(min_row=start_row, min_col=stat_idx, max_col=stat_idx, max_row=start_row + len(investment_options) - 1):
        for cell in row:
            cell.fill = PatternFill()

    # Match and write
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

# =====================================
# Streamlit UI
# =====================================
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
        st.write("🔍 Raw PDF Data Extracted:", pdf_data)
        st.success(f"✅ Extracted {len(pdf_data)} funds from PDF")

        try:
            st.info("Updating Excel...")
            updated_wb = apply_status_to_excel(excel_file, sheet_name, investment_options, pdf_data)

            output = io.BytesIO()
            updated_wb.save(output)
            st.download_button("📥 Download Updated Excel", output.getvalue(), file_name="Updated_Fund_Scorecard.xlsx")

        except Exception as e:
            st.error(f"❌ Failed to update Excel: {e}")
