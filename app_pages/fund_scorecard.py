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
        
        # Only allow single letter for column input
        raw_col = st.text_input("Start Column (e.g. 'B')", max_chars=1)
        start_col = raw_col.upper().strip() if raw_col else ""
        if raw_col and (not start_col.isalpha() or len(start_col) != 1):
            st.warning("Please enter a single letter column (A-Z).")
            start_col = ""

        start_row = st.number_input("Start Row (where data begins)", min_value=1)
        start_page = st.number_input("Start Page in PDF", min_value=1)
        end_page = st.number_input("End Page in PDF", min_value=1)

    # --- Extracted Fund Name Preview ---
    with st.expander("3. Preview Fund Names from PDF"):
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
            fund_names_input = st.text_area("Edit Fund Names (one per line)", "\n".join(unique_names))
            fund_names = [name.strip() for name in fund_names_input.splitlines() if name.strip()]

        except Exception as e:
            st.error("Failed to extract text from PDF. Try adjusting the page range.")
            st.stop()

    # --- Preview Mode ---
    dry_run = st.checkbox("Dry Run (preview changes only)", value=True)

    # --- Run Button ---
    if st.button("Generate Scorecard"):
        with st.spinner("Processing..."):
            try:
                result_df = update_excel_with_template(
                    pdf_bytes=pdf_file.read(),
                    excel_bytes=excel_file.read(),
                    sheet_name=sheet_name,
                    status_col=start_col,
                    start_row=start_row,
                    fund_names=fund_names,
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
