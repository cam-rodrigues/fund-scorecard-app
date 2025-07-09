import streamlit as st
import pandas as pd
import pdfplumber
import io
from rapidfuzz import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.cell import coordinate_to_tuple

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
                        fund_data.append((fund_name,))  # Will get skipped later if malformed
    return fund_data

# =============================
# Excel Coloring — 100% Safe
# =============================
def update_excel(excel_file, sheet_name, fund_data, investment_options, status_cell):
    wb = load_workbook(excel_file)
    ws = wb[sheet_name]

    try:
        start_row, col_index = coordinate_to_tuple(status_cell)
    except Exception as e:
        raise ValueError("Invalid cell reference for status cell.")

    # ✅ SAFE unpacking with check
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
        if match_result:
            best_match, score = match_result
        else:
            best_match, score = None, 0

        status = fund_dict.get(best_match) if score >= 85 else ""
        cell = ws.cell(row=start_row + i, column=col_index)
        cell.value = status
        cell.fill = green if status == "Pass" else red if status == "Review" else PatternFill()

        results.append({
            "Your Input": fund,
            "Matched Fund": best_match or "",
            "Status": status or "",
            "Match Score": round(score, 1)
        })

    return wb, results

# =============================
# Streamlit App
# =============================
def run():
    st.title("✅ FidSync: Fund Scorecard Matching (Safe Version)")

    st.markdown("""
    Upload a **PDF fund scorecard** and matching **Excel sheet**, paste your Investment Options,
    and enter the **starting cell** where the column "Current Quarter Status" is located (e.g., `E5`).
    """)

    pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type="pdf")
    excel_file = st.file_uploader("Upload Excel File", type="xlsx")

    investment_input = st.text_area("Paste Investment Options (one per line):")
    investment_options = [line.strip() for line in investment_input.split("\n") if line.strip()]

    if excel_file:
        xls = pd.ExcelFile(excel_file)
        sheet_name = st.selectbox("Select Excel Sheet", xls.sheet_names)
    else:
        sheet_name = None

    status_cell = st.text_input("Enter starting cell for 'Current Quarter Status' column (e.g. E5)")

    if st.button("Run Matching"):
        if not pdf_file or not excel_file or not investment_options or not status_cell or not sheet_name:
            st.error("Please provide all inputs above.")
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
            st.success("✅ Excel updated successfully.")
            st.download_button("📥 Download Updated Excel", output.getvalue(), file_name="Updated_Fund_Scorecard.xlsx")
        except Exception as e:
            st.error(f"❌ Failed to update Excel: {str(e)}")
