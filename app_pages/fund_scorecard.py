import streamlit as st
import pandas as pd
from utils.pdf_utils import extract_data_from_pdf
from utils.excel_utils import update_excel_with_template
from io import StringIO
import tempfile
import os


def run():
    st.title("📊 FidSync Fund Scorecard")
    st.markdown("Easily extract fund names from a PDF report and align them with investment options in your Excel template.")

    with st.expander("ℹ️ How it works", expanded=False):
        st.markdown("""
        **What this tool does:**
        1. Extracts fund names from PDF (e.g., MPI reports).
        2. Matches those funds with your investment options.
        3. Updates your Excel scorecard with a clear Pass/Fail summary.
        """)

    # Step 1 – Upload Files
    st.markdown("### 🧾 Step 1: Upload Report and Excel Template")
    col1, col2 = st.columns(2)
    with col1:
        pdf_file = st.file_uploader("Upload PDF report", type=["pdf"])
    with col2:
        excel_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

    # Step 2 – Select Pages
    st.markdown("### 📄 Step 2: Select PDF Page Range")
    start_page = st.number_input("Start Page", min_value=1, step=1)
    end_page = st.number_input("End Page", min_value=start_page, step=1)

    # Step 3 – Enter Investment Options
    st.markdown("### 📋 Step 3: Provide Investment Options")

    mode = st.radio("Choose input method", ["Paste manually", "Upload CSV"])
    investment_options = []

    if mode == "Paste manually":
        manual_input = st.text_area("Enter one investment option per line", height=150, placeholder="E.g.\nOption A\nOption B")
        investment_options = [line.strip() for line in manual_input.split("\n") if line.strip()]
    else:
        uploaded_csv = st.file_uploader("Upload CSV file with investment options", type=["csv"])
        if uploaded_csv:
            df_csv = pd.read_csv(uploaded_csv)
            investment_options = df_csv.iloc[:, 0].dropna().tolist()

    # Run Process
    if st.button("🚀 Run Scorecard"):
        if not (pdf_file and excel_file and investment_options and start_page <= end_page):
            st.warning("Please complete all inputs.")
            return

        with st.spinner("Extracting and matching funds..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(pdf_file.read())
                    temp_pdf_path = temp_pdf.name

                fund_names = extract_data_from_pdf(temp_pdf_path, int(start_page), int(end_page))

                if len(fund_names) != len(investment_options):
                    st.warning(f"⚠️ Fund count ({len(fund_names)}) does not match investment option count ({len(investment_options)}). Please check for alignment.")

                match_df = pd.DataFrame({
                    "Extracted Fund Name": fund_names,
                    "Investment Option": investment_options[:len(fund_names)]
                })

                st.markdown("### 🔍 Match Preview")
                st.dataframe(match_df, use_container_width=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_xlsx:
                    temp_xlsx.write(excel_file.read())
                    temp_xlsx_path = temp_xlsx.name

                update_excel_with_template(temp_xlsx_path, match_df)

                with open(temp_xlsx_path, "rb") as f:
                    st.success("✅ Scorecard updated successfully!")
                    st.download_button("📥 Download Updated Excel", f.read(), file_name="Updated_Fund_Scorecard.xlsx")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
