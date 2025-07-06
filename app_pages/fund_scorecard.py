import streamlit as st
import pandas as pd
import pdfplumber
import os
import sys
import io
from difflib import SequenceMatcher

# Add utils path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.excel_utils import update_excel_with_template
from utils.pdf_utils import extract_data_from_pdf


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def run():
    st.header("Fund Scorecard")

    # --- File Upload ---
    with st.expander("1. Upload Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("Upload Fund PDF", type=["pdf"])
        with col2:
            excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    if not pdf_file or not excel_file:
        st.info("Please upload both a PDF and an Excel file to continue.")
        return

    # --- Settings ---
    with st.expander("2. Configure Settings", expanded=True):
        sheet_name = st.text_input("Excel Sheet Name")
        raw_col = st.text_input("Start Column (e.g. 'B')", max_chars=1)
        start_col = raw_col.upper().strip() if raw_col else ""
        if raw_col and (not start_col.isalpha() or len(start_col) != 1):
            st.warning("Please enter a single letter column (A-Z).")
            start_col = ""
        start_row = st.number_input("Start Row (where data begins)", min_value=1)
        start_page = st.number_input("Start Page in PDF", min_value=1)
        end_page = st.number_input("End Page in PDF", min_value=1)

    # --- Matching Section ---
    with st.expander("3. Match Fund Names with Investment Options", expanded=True):
        extracted_names, fund_names = [], []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                pages = pdf.pages[int(start_page) - 1:int(end_page)]
                for page in pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            if "fund" in line.lower() and len(line.strip()) < 80:
                                extracted_names.append(line.strip())
            fund_names = sorted(set(extracted_names))
            show_names = st.checkbox("Show extracted fund names", value=True)
            if show_names:
                fund_names_input = st.text_area("Fund Names", "\n".join(fund_names), height=200)
                fund_names = [name.strip() for name in fund_names_input.splitlines() if name.strip()]

            use_csv = st.checkbox("Upload CSV of Investment Options")
            investment_options = []
            if use_csv:
                csv_file = st.file_uploader("Upload CSV File", type=["csv"])
                if csv_file:
                    try:
                        df = pd.read_csv(csv_file)
                        col_name = st.selectbox("Select column", df.columns)
                        investment_options = df[col_name].dropna().astype(str).tolist()
                        st.success(f"✅ Loaded {len(investment_options)} options from CSV.")
                    except Exception as e:
                        st.error("Failed to read CSV.")
                        st.exception(e)
            else:
                with st.expander("Why do I have to paste these manually?"):
                    st.markdown("""
We can't automatically extract investment option names from Excel because:
- They're often stored as formulas like `=A1`
- Layouts are inconsistent
- Headers may be missing
- Merged cells break detection

Paste one per line to ensure accuracy.
""")
                investment_input = st.text_area("Paste Investment Options", "", height=200)
                investment_options = [line.strip() for line in investment_input.splitlines() if line.strip()]
                if any(line.startswith("=") for line in investment_options):
                    st.warning("Some lines look like Excel formulas. Paste plain text only.")

        except Exception as e:
            st.error("Error reading PDF.")
            st.exception(e)
            return

        if fund_names and investment_options:
            st.subheader("🔍 Match Preview")
            if len(fund_names) != len(investment_options):
                st.error("Mismatch: different number of fund names and investment options.")
                st.markdown("### ⚠️ Potential Matches (Top Similarities)")
                mismatch_preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Closest Match": [
                        max(investment_options, key=lambda opt: similar(fund, opt))
                        for fund in fund_names
                    ]
                })
                st.dataframe(mismatch_preview)
            else:
                match_preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Investment Option": investment_options
                })
                st.dataframe(match_preview)

    dry_run = st.checkbox("Dry Run (preview only)", value=True)

    if st.button("Generate Scorecard"):
        if len(fund_names) != len(investment_options):
            st.error("Mismatch: line counts must match.")
            return
        try:
            with st.spinner("Processing..."):
                result_df = update_excel_with_template(
                    pdf_bytes=pdf_file.read(),
                    excel_bytes=excel_file.read(),
                    sheet_name=sheet_name,
                    status_col=start_col,
                    start_row=start_row,
                    fund_names=investment_options,
                    start_page=start_page,
                    end_page=end_page,
                    dry_run=dry_run,
                )
                st.success("Done!")
                st.dataframe(result_df)
                if not dry_run:
                    st.download_button(
                        label="Download Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error("Error while generating scorecard.")
            st.exception(e)
