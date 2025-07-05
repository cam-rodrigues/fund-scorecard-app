import streamlit as st
import io
import base64
import pandas as pd
import gc
from utils.pdf_utils import extract_fund_status
from utils.excel_utils import update_excel_with_status
from utils.logger import log_action

st.title("Fund Scorecard Status Tool")

if st.button("Reset"):
    st.experimental_set_query_params(reset="true")
    st.experimental_rerun()

with st.form("upload_form"):
    st.subheader("Upload Files")
    pdf_file = st.file_uploader("Upload Fund Scorecard PDF", type=["pdf"])
    excel_file = st.file_uploader("Upload Excel Workbook", type=["xlsx", "xlsm"])

    st.subheader("Settings")
    col1, col2, col3 = st.columns(3)
    sheet_name = col1.text_input("Excel Sheet Name")
    status_col = col2.text_input("Starting Column Letter").strip().upper()
    start_row = col3.number_input("Starting Row Number", min_value=1)

    col4, col5 = st.columns(2)
    start_page = col4.number_input("Start Page in PDF", min_value=1)
    end_page = col5.number_input("End Page in PDF", min_value=1)

    fund_names_input = st.text_area("Investment Option Names (One Per Line)", height=200)
    dry_run = st.checkbox("Dry Run (preview only, don't update Excel)", value=False)

    submitted = st.form_submit_button("Run Status Update")

if submitted:
    if not pdf_file or not excel_file:
        st.warning("Please upload both PDF and Excel files.")
    elif start_page > end_page:
        st.error("Start Page must be less than or equal to End Page.")
    elif not fund_names_input.strip():
        st.warning("Please enter investment option names.")
    else:
        with st.spinner("Processing..."):
            try:
                fund_names = [line.strip() for line in fund_names_input.strip().splitlines() if line.strip()]
                pdf_bytes = pdf_file.read()
                excel_bytes = excel_file.read()

                updated_excel, count, match_log = update_excel_with_status(
                    pdf_bytes, excel_bytes, sheet_name, status_col,
                    start_row, fund_names, start_page, end_page,
                    dry_run
                )

                log_action(
                    user="anonymous",  # Replace with user login later if needed
                    action="Ran Fund Scorecard Update",
                    details=f"{len(fund_names)} funds, sheet: {sheet_name}, dry_run={dry_run}"
                )

                if dry_run:
                    st.info("Dry run complete. No changes were made to the Excel file.")
                else:
                    st.success(f"Successfully updated {count} row(s).")

                    b64 = base64.b64encode(updated_excel.getvalue()).decode()
                    link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Updated_Investment_Status.xlsx">Download Updated Excel</a>'
                    st.markdown(link, unsafe_allow_html=True)

                st.markdown("### Match Log")
                df_log = pd.DataFrame(match_log, columns=["Input Name", "Matched Name", "Match Score", "Status"])
                st.dataframe(df_log)

                csv_buffer = io.StringIO()
                df_log.to_csv(csv_buffer, index=False)
                csv_b64 = base64.b64encode(csv_buffer.getvalue().encode()).decode()
                csv_link = f'<a href="data:file/csv;base64,{csv_b64}" download="match_log.csv">Download Match Log CSV</a>'
                st.markdown(csv_link, unsafe_allow_html=True)

                del pdf_bytes, excel_bytes, updated_excel, df_log
                gc.collect()

            except Exception as e:
                st.error("Something went wrong.")
                st.exception(e)
