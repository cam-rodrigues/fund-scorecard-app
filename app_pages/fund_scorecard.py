import streamlit as st
import pandas as pd
import pdfplumber
import io
from rapidfuzz import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.cell import coordinate_to_tuple
import zipfile

# =============================
# PDF Extraction — Bulletproof
# =============================
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
                        fund_data.append((fund_name, status))
                    else:
                        fund_data.append((fund_name,))
    return fund_data

# =============================
# Excel Matching + Coloring
# =============================
def update_excel(excel_file, sheet_name, fund_data, investment_options, status_cell):
    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    try:
        start_row, col_index = coordinate_to_tuple(status_cell)
    except Exception:
        raise ValueError("Invalid cell reference for status cell.")

    fund_dict = {}
    for item in fund_data:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            name, status = item
            fund_dict[str(name).strip()] = str(status).strip()
        else:
            st.warning(f"⚠️ Skipped malformed entry: {item}")

    green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    results = []
    for i, fund in enumerate(investment_options):
        fund = fund.strip()
        if not fund:
            continue

        match_result = process.extractOne(fund, fund_dict.keys(), scorer=fuzz.token_sort_ratio)
        best_match, score = match_result if match_result else (None, 0)

        status = fund_dict.get(best_match) if score >= 20 else ""

        cell = ws.cell(row=start_row + i, column=col_index)
        cell.value = None  # remove formulas or weird symbols

        if status == "Pass":
            cell.fill = green
        elif status == "Review":
            cell.fill = red
        else:
            cell.fill = PatternFill(fill_type=None)

        results.append({
            "Your Input": fund,
            "Matched Fund": best_match or "",
            "Status": status or "",
            "Match Score": round(score, 1)
        })

    return wb, results

# =============================
# Check for External Links
# =============================
def has_external_links(xlsx_file):
    try:
        with zipfile.ZipFile(xlsx_file) as zf:
            return any(name.startswith("xl/externalLinks/") for name in zf.namelist())
    except:
        return False

# =============================
# Streamlit App
# =============================
def run():
    st.title("✅ FidSync: Fund Scorecard Matching")

    pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type="pdf")
    excel_file = st.file_uploader("Upload Excel File", type="xlsx")

    if excel_file and has_external_links(excel_file):
        st.warning("""
        ⚠️ **Notice About Linked Excel Files**

        This file contains **external references** to other workbooks (e.g., formulas linked to another Excel file).

        When you download the updated version, Excel will display warnings like:
        - “We found a problem with some content...”
        - “Do you want us to try to recover...”

        👉 This is **normal**. Just click **Yes** and then **Enable Editing** when prompted — your file will open correctly.
        """)

    investment_input = st.text_area("Paste Investment Options (one per line):")
    investment_options = [line.strip() for line in investment_input.split("\n") if line.strip()]

    if excel_file:
        xls = pd.ExcelFile(excel_file)
        sheet_name = st.selectbox("Select Excel Sheet", xls.sheet_names)
    else:
        sheet_name = None

    status_cell = st.text_input("Enter starting cell for 'Current Quarter Status' column (e.g. L6)")

    if st.button("Run Matching"):
        if not pdf_file or not excel_file or not investment_options or not status_cell or not sheet_name:
            st.error("Please provide all required inputs.")
            return

        try:
            fund_data = extract_funds_from_pdf(pdf_file)
            if not fund_data:
                st.warning("No funds extracted from PDF.")
                return

            wb, match_results = update_excel(excel_file, sheet_name, fund_data, investment_options, status_cell)

            st.subheader("🔍 Match Preview")
            st.dataframe(pd.DataFrame(match_results))

            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            st.success("✅ Excel updated successfully.")
            st.download_button("📥 Download Updated Excel", data=output, file_name="Updated_Fund_Scorecard.xlsx")

        except Exception as e:
            st.error(f"❌ Failed to update Excel: {str(e)}")
