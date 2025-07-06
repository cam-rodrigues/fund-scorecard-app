import streamlit as st
import pandas as pd
from utils.pdf_utils import extract_data_from_pdf
from utils.excel_utils import update_excel_with_template
from io import StringIO
import tempfile
import os

def run():
    st.title("📊 FidSync Fund Scorecard")
    st.markdown("A clean, accurate way to extract fund names from PDF reports, align them with investment options, and update your Excel templates — no Excel hacks required.")

    with st.expander("ℹ️ How it Works", expanded=False):
        st.markdown("""
        **What this tool does:**
        1. Extracts fund names from PDF (e.g., MPI reports)
        2. Matches them to your investment options
        3. Updates your Excel scorecard with a clear Pass/Fail summary
        """)

    # Step 1 – Upload Files
    st.subheader("🧾 Step 1: Upload Report and Excel Template")
    col1, col2 = st.columns(2)
    with col1:
        pdf_file = st.file_uploader("Upload PDF report", type=["pdf"])
    with col2:
        excel_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

    # Step 2 – Select Pages
    st.subheader("📄 Step 2: Select PDF Page Range")
    start_page = st.number_input("Start Page", min_value=1, step=1)
    end_page = st.number_input("End Page", min_value=start_page, step=1)

    # Step 3 – Enter Investment Options
    st.subheader("📋 Step 3: Provide Investment Options")

    mode = st.radio("Choose input method:", ["Paste manually", "Upload CSV"])
    investment_options = []

    if mode == "Paste manually":
        manual_input = st.text_area(
            "Enter one investment option per line:",
            placeholder="Example:\nOption A\nOption B",
            height=150
        )
        investment_options = [line.strip() for line in manual_input.split("\n") if line.strip()]
    else:
        uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_csv:
            try:
                df_csv = pd.read_csv(uploaded_csv)
                investment_options = df_csv.iloc[:, 0].dropna().tolist()
            except Exception as e:
                st.error(f"Could not read CSV: {e}")

    # Step 4 – Process and Display Results
    st.subheader("✅ Step 4: Run the Scorecard")
    if st.button("🚀 Run Scorecard"):
        if not (pdf_file and excel_file and investment_options and start_page <= end_page):
            st.warning("Please complete all inputs correctly.")
            return

        with st.spinner("Processing fund data..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(pdf_file.read())
                    temp_pdf_path = temp_pdf.name

                fund_names = extract_data_from_pdf(temp_pdf_path, int(start_page), int(end_page))

                if not fund_names:
                    st.error("No fund names were extracted from the selected page range.")
                    return

                if len(fund_names) != len(investment_options):
                    st.warning(f"⚠️ Mismatch: {len(fund_names)} fund(s) vs {len(investment_options)} investment option(s)")

                match_df = pd.DataFrame({
                    "Extracted Fund Name": fund_names,
                    "Investment Option": investment_options[:len(fund_names)]
                })

                st.markdown("### 🔍 Preview of Matched Results")
                st.dataframe(match_df, use_container_width=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_excel:
                    temp_excel.write(excel_file.read())
                    temp_excel_path = temp_excel.name

                update_excel_with_template(temp_excel_path, match_df)

                with open(temp_excel_path, "rb") as updated_file:
                    st.download_button(
                        label="📥 Download Updated Excel",
                        data=updated_file,
                        file_name="Updated_Fund_Scorecard.xlsx"
                    )

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
