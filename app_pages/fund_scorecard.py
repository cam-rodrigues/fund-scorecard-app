import streamlit as st
import pandas as pd
import pdfplumber
import io
from difflib import SequenceMatcher
from utils.excel_utils import update_excel_with_template
from utils.pdf_utils import extract_data_from_pdf

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def run():
    st.markdown("## 🧾 Fund Scorecard Tool")

    st.markdown("""
        <style>
            .section-box {
                background-color: #f9f9f9;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                margin-bottom: 2rem;
            }
            .section-title {
                font-size: 1.3rem;
                font-weight: 600;
                color: #1e88e5;
                margin-bottom: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">1. Upload Files</div>', unsafe_allow_html=True)

        pdf_file = st.file_uploader("Upload Fund PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Template", type=["xlsx", "xlsm"])
        sheet_name = st.text_input("Excel Sheet Name (exact)", value="Current Period")
        start_page = st.number_input("Start Page", min_value=1, value=1)
        end_page = st.number_input("End Page", min_value=start_page, value=start_page+1)

        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">2. Provide Investment Options</div>', unsafe_allow_html=True)

        hide_options = st.checkbox("Hide raw fund names textarea", value=False)
        investment_input_method = st.radio("Choose input method", ["Paste from Clipboard", "Upload CSV"])

        investment_options = []

        if investment_input_method == "Paste from Clipboard":
            pasted_text = st.text_area("Paste investment options (one per line)", height=150, label_visibility="collapsed" if hide_options else "visible")
            if pasted_text:
                investment_options = [line.strip() for line in pasted_text.strip().split("\n") if line.strip()]
        else:
            csv_file = st.file_uploader("Upload CSV with Investment Options", type=["csv"], key="csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    investment_options = df.iloc[:, 0].dropna().astype(str).tolist()
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Run Match"):
        if not (pdf_file and excel_file and investment_options):
            st.warning("Please upload all files and provide investment options before running.")
            return

        with st.spinner("Extracting fund names from PDF..."):
            try:
                pdf_bytes = io.BytesIO(pdf_file.read())
                fund_names = extract_data_from_pdf(pdf_bytes, start_page, end_page)
            except Exception as e:
                st.error(f"Failed to extract fund names from PDF: {e}")
                return

        st.success(f"Extracted {len(fund_names)} fund names from PDF.")

        # Match fund names to investment options using fuzzy logic
        matches = []
        for raw_fund in fund_names:
            best_match = max(investment_options, key=lambda opt: similar(raw_fund, opt))
            score = similar(raw_fund, best_match)
            status = "Pass" if score >= 0.8 else "Fail"
            matches.append({"Fund Name (Raw)": raw_fund, "Matched Option": best_match, "Score": round(score, 2), "Status": status})

        result_df = pd.DataFrame(matches)

        st.markdown("### 🔍 Match Preview")
        st.dataframe(
            result_df.style
                .applymap(lambda val: 'background-color: #d0f0c0' if val == 'Pass' else ('background-color: #f8d7da' if val == 'Fail' else ''), subset=["Status"])
                .format({"Score": "{:.2f}"})
        )

        if st.button("Export to Excel"):
            try:
                excel_bytes = io.BytesIO(excel_file.read())
                output = update_excel_with_template(excel_bytes, sheet_name, result_df)
                st.download_button("📥 Download Updated Excel", data=output, file_name="FidSync_Scorecard.xlsx")
                st.success("Excel updated successfully.")
            except Exception as e:
                st.error(f"Export failed: {e}")
