import streamlit as st
import pandas as pd
import pdfplumber
import sys
import os

# Make utils work in Streamlit Cloud
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.excel_utils import update_excel_with_status


def run():
    st.header("Fund Scorecard")
    st.markdown("Upload a fund PDF and Excel template to auto-generate your scorecard.")

    # --- Upload Section ---
    with st.expander("Upload Files", expanded=True):
        pdf_file = st.file_uploader("Upload Fund PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    # --- PDF Preview and Auto-Extraction ---
    if pdf_file:
        with st.expander("Preview PDF Pages and Auto-Extract Fund Names"):
            preview_start = st.number_input("Preview from page", value=1, min_value=1)
            preview_end = st.number_input("Preview to page", value=3, min_value=1)

            preview_button = st.button("Show Preview & Extract Fund Names")

            if preview_button:
                try:
                    with pdfplumber.open(pdf_file) as pdf:
                        total_pages = len(pdf.pages)
                        start = max(0, preview_start - 1)
                        end = min(preview_end, total_pages)

                        st.write(f"Showing pages {preview_start}–{preview_end} of {total_pages}")
                        extracted_names = []

                        for i in range(start, end):
                            text = pdf.pages[i].extract_text()
                            if text:
                                st.text_area(f"Page {i + 1} Text", text, height=150, key=f"preview_{i}")

                                lines = text.split("\n")
                                for line in lines:
                                    if "fund" in line.lower() and len(line.strip()) < 80:
                                        extracted_names.append(line.strip())

                        if extracted_names:
                            unique_names = sorted(set(extracted_names))
                            joined = "\n".join(unique_names)
                            st.session_state["auto_fund_names"] = joined
                            st.success("Fund names extracted — see below.")
                        else:
                            st.warning("No fund-like lines found in selected pages.")

                except Exception as e:
                    st.error("Error while reading the PDF.")
                    st.exception(e)

    # --- Configuration Section ---
    with st.expander("Configuration", expanded=True):
        sheet_name = st.text_input("Sheet name in Excel")
        status_col = st.text_input("Column name for status updates")
        start_row = st.number_input("Start row (first data row)", min_value=1)
        start_page = st.number_input("Start page in PDF", min_value=1)
        end_page = st.number_input("End page in PDF", min_value=1)

        default_names = st.session_state.get("auto_fund_names", "")
        fund_names_input = st.text_area("List of fund names (one per line)", value=default_names)
        fund_names = [name.strip() for name in fund_names_input.splitlines() if name.strip()]

        dry_run = st.checkbox("Dry run (show results without saving to file)", value=False)

    # --- Process Button ---
    if st.button("Generate Scorecard"):
        if not pdf_file or not excel_file:
            st.warning("Please upload both a PDF and an Excel file.")
            return

        with st.spinner("Processing..."):
            try:
                result_df = update_excel_with_status(
                    pdf_bytes=pdf_file.read(),
                    excel_bytes=excel_file.read(),
                    sheet_name=sheet_name,
                    status_col=status_col,
                    start_row=int(start_row),
                    fund_names=fund_names,
                    start_page=int(start_page),
                    end_page=int(end_page),
                    dry_run=dry_run
                )

                st.success("Scorecard updated successfully.")
                st.dataframe(result_df, use_container_width=True)

                if not dry_run:
                    st.download_button(
                        label="Download Updated Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error("Something went wrong.")
                st.exception(e)
