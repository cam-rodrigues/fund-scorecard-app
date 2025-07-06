import streamlit as st
import pandas as pd
from utils.pdf_utils import extract_data_from_pdf
from utils.excel_utils import update_excel_with_template
import tempfile

def run():
    st.title("Fund Scorecard Tool")
    st.write("Process PDF reports, match fund names to your investment options, and update your Excel scorecard automatically.")

    with st.expander("How it Works", expanded=False):
        st.markdown("""
        This tool:
        1. Extracts fund names from your PDF report
        2. Matches them to investment options
        3. Updates an Excel file with Pass/Fail indicators
        """)

    st.subheader("1. Upload Files")
    col1, col2 = st.columns(2)
    with col1:
        pdf_file = st.file_uploader("Upload PDF Report", type=["pdf"])
    with col2:
        excel_file = st.file_uploader("Upload Excel File", type=["xlsx", "xlsm"])

    st.subheader("2. Select Page Range")
    start_page = st.number_input("Start Page", min_value=1, step=1)
    end_page = st.number_input("End Page", min_value=start_page, step=1)

    st.subheader("3. Provide Investment Options")
    mode = st.radio("Input Method", ["Paste manually", "Upload CSV"])
    investment_options = []

    if mode == "Paste manually":
        text_input = st.text_area("Enter one investment option per line", height=150)
        investment_options = [line.strip() for line in text_input.split("\n") if line.strip()]
    else:
        csv_file = st.file_uploader("Upload CSV", type=["csv"])
        if csv_file:
            try:
                df = pd.read_csv(csv_file)
                investment_options = df.iloc[:, 0].dropna().tolist()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    st.subheader("4. Run the Scorecard")
    if st.button("Run Scorecard"):
        if not (pdf_file and excel_file and investment_options and start_page <= end_page):
            st.warning("Please complete all required inputs.")
            return

        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(pdf_file.read())
                    pdf_path = tmp_pdf.name

                fund_names = extract_data_from_pdf(pdf_path, int(start_page), int(end_page))

                if not fund_names:
                    st.error("No fund names found.")
                    return

                if len(fund_names) != len(investment_options):
                    st.warning(f"Mismatch: {len(fund_names)} funds vs {len(investment_options)} options")

                results = pd.DataFrame({
                    "Extracted Fund Name": fund_names,
                    "Investment Option": investment_options[:len(fund_names)]
                })

                st.markdown("### Preview of Matched Funds")
                st.dataframe(results, use_container_width=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
                    tmp_xlsx.write(excel_file.read())
                    excel_path = tmp_xlsx.name

                update_excel_with_template(excel_path, results)

                with open(excel_path, "rb") as updated_file:
                    st.download_button(
                        label="Download Updated Excel",
                        data=updated_file,
                        file_name="Updated_Fund_Scorecard.xlsx"
                    )

            except Exception as e:
                st.error(f"An error occurred: {e}")
