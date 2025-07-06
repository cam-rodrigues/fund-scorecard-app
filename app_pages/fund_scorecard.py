import streamlit as st
import pandas as pd
import pdfplumber
import os
import sys
import io

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.excel_utils import update_excel_with_template
from utils.pdf_utils import extract_data_from_pdf


def run():
    st.header("Fund Scorecard")

    # --- File Upload ---
    with st.expander("1. Upload Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("Upload Fund PDF", type=["pdf"], key="pdf_upload")
        with col2:
            excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"], key="excel_upload")

    if not pdf_file or not excel_file:
        st.info("Please upload both a PDF and an Excel file to continue.")
        return

    # --- Configuration ---
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

    # --- Fund Name Extraction + Investment Options ---
    with st.expander("3. Fund Names + Investment Options"):
        extracted_names = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                pages = pdf.pages[int(start_page)-1:int(end_page)]
                for page in pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            if "fund" in line.lower() and len(line.strip()) < 80:
                                extracted_names.append(line.strip())

            unique_names = sorted(set(extracted_names))
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Fund Names Extracted from PDF**")
                fund_names_input = st.text_area(
                    "Fund Names",
                    "\n".join(unique_names),
                    height=200
                )

            with col2:
                st.markdown("**Paste Investment Options from Excel**")
                with st.expander("Why do I have to paste these manually?"):
                    st.markdown("""
We can't automatically extract investment option names from Excel because:

- The names are often stored as **formulas** (like `=A1`) instead of plain text, which this app can’t read
- The layout of the Excel files is often inconsistent
- Headers are missing or unclear
- Cells may be **merged** or scattered across the sheet

To ensure accuracy, please paste the investment options manually — one per line, in the same order as the fund names.

📌 *Example from Excel:*
Growth Fund A
Stable Value Option
International Equity Fund""")

                investment_input = st.text_area(
                    "Investment Options",
                    "",
                    height=200,
                    help="Paste exactly one investment option per line. Match the order of fund names shown on the left."
                )

                # 🧠 Live Count and Formula Warning
                investment_lines = [line.strip() for line in investment_input.splitlines() if line.strip()]
                st.caption(f"📝 {len(investment_lines)} investment option(s) entered.")

                if any(line.startswith("=") for line in investment_lines):
                    st.warning("Some lines look like Excel formulas (e.g. `=A1`). Please paste plain text instead.")

            fund_names = [name.strip() for name in fund_names_input.splitlines() if name.strip()]
            investment_options = investment_lines

        except Exception as e:
            st.error("Failed to extract text from PDF. Try adjusting the page range.")
            st.exception(e)
            st.stop()

    # --- Preview Mode ---
    dry_run = st.checkbox("Dry Run (preview changes only)", value=True)

    # --- Generate Button ---
    if st.button("Generate Scorecard"):
        if len(fund_names) != len(investment_options):
            st.error("The number of investment options must match the number of fund names.")
            return

        with st.spinner("Processing..."):
            try:
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

                st.success("Done! See preview below." if dry_run else "File updated successfully.")
                st.dataframe(result_df, use_container_width=True)

                if not dry_run:
                    st.download_button(
                        label="Download Updated Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error("Something went wrong while generating the scorecard.")
                st.exception(e)


