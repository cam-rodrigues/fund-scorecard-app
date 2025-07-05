import streamlit as st
import pandas as pd
import sys
import os

# 🔧 Make sure utils can be imported (works on Streamlit Cloud)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.excel_utils import update_excel_with_status
from utils.pdf_utils import extract_data_from_pdf  # keep this if you're still using it

def run():
    st.header("📊 Fund Scorecard")
    st.markdown("Upload a PDF and Excel file, and update the fund status columns based on matches.")

    with st.expander("🔍 Upload Files", expanded=True):
        pdf_file = st.file_uploader("Upload Fund PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    with st.expander("⚙️ Configuration", expanded=True):
        sheet_name = st.text_input("Sheet name in Excel", value="Scorecard")
        status_col = st.text_input("Column name for status updates", value="Status")
        start_row = st.number_input("Start row (first data row)", value=2, min_value=1)
        start_page = st.number_input("Start page in PDF", value=1, min_value=1)
        end_page = st.number_input("End page in PDF", value=3, min_value=1)

        fund_names_input = st.text_area("List of fund names (one per line)", value="Fund A\nFund B")
        fund_names = [name.strip() for name in fund_names_input.splitlines() if name.strip()]

        dry_run = st.checkbox("Dry run (show results without saving to file)", value=False)

    if st.button("Generate Scorecard"):
        if not pdf_file or not excel_file:
            st.warning("Please upload both a PDF and an Excel file.")
            return

        with st.spinner("Processing files and updating scorecard..."):
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

                st.success("✅ Scorecard updated successfully!")
                st.dataframe(result_df, use_container_width=True)

                if not dry_run:
                    st.download_button(
                        label="⬇️ Download Updated Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error("❌ Something went wrong during processing.")
                st.exception(e)
