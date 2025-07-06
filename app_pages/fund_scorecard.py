import streamlit as st
import pandas as pd
import pdfplumber
import os
import sys
from difflib import SequenceMatcher

# Add utils path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.excel_utils import update_excel_with_template
from utils.pdf_utils import extract_data_from_pdf


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def run():
    st.markdown("<h1 style='text-align: center;'>📊 FidSync Fund Scorecard</h1>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Help Section ---
    with st.expander("ℹ️ How to Use This Tool", expanded=False):
        st.markdown("""
**What This Does:**
- Pulls fund names from a multi-page PDF
- Lets you paste investment options (we can't extract those from Excel reliably)
- Inserts Pass/Fail data into an Excel template

**Steps:**
1. Upload your PDF and Excel
2. Configure where to write data
3. Paste investment options (or upload a CSV)
4. Match, preview, and generate your file
""")

    # --- Step 1: Upload Files ---
    with st.container():
        st.subheader("1. Upload Your Files")
        st.caption("Upload both the PDF report and Excel template below.")
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("📄 PDF Report", type=["pdf"])
        with col2:
            excel_file = st.file_uploader("📊 Excel Template", type=["xlsx"])

    if not pdf_file or not excel_file:
        st.info("Upload both a PDF and an Excel file to continue.")
        return

    # --- Step 2: Configure Excel + PDF Settings ---
    with st.container():
        st.subheader("2. Configure Excel + PDF Settings")
        st.caption("These tell the app where to start writing in Excel and which pages to extract.")

        col1, col2, col3 = st.columns(3)
        with col1:
            sheet_name = st.text_input("Sheet Name")
        with col2:
            start_col = st.text_input("Start Column (A–Z)", max_chars=1).upper().strip()
        with col3:
            start_row = st.number_input("Start Row (e.g. 2)", min_value=1, step=1)

        col4, col5 = st.columns(2)
        with col4:
            start_page = st.number_input("PDF Start Page", min_value=1, step=1)
        with col5:
            end_page = st.number_input("PDF End Page", min_value=1, step=1)

        if start_col and (not start_col.isalpha() or len(start_col) != 1):
            st.warning("Start Column must be one letter (A–Z).")
            return

    # --- Step 3: Fund Names + Investment Options ---
    with st.container():
        st.subheader("3. Fund Names + Investment Options")

        fund_names = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                pages = pdf.pages[start_page - 1:end_page]
                lines = []
                for p in pages:
                    text = p.extract_text()
                    if text:
                        lines.extend([l.strip() for l in text.split("\n") if "fund" in l.lower()])
                fund_names = sorted(set(lines))

            st.success(f"✅ {len(fund_names)} fund name(s) extracted from the PDF.")
            if st.checkbox("Edit Fund Names", value=True):
                fund_input = st.text_area("Fund Names", "\n".join(fund_names), height=180)
                fund_names = [f.strip() for f in fund_input.splitlines() if f.strip()]
        except Exception as e:
            st.error("PDF extraction failed.")
            st.exception(e)
            return

        st.caption("Provide Investment Options")
        input_method = st.radio("Choose how to enter options:", ["Paste Manually", "Upload CSV"], horizontal=True)

        investment_options = []
        if input_method == "Upload CSV":
            csv_file = st.file_uploader("Upload CSV File", type="csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    selected_col = st.selectbox("Select column", df.columns)
                    investment_options = df[selected_col].dropna().astype(str).tolist()
                    st.success(f"✅ Loaded {len(investment_options)} options.")
                except Exception as e:
                    st.error("Could not read the CSV.")
                    st.exception(e)
        else:
            with st.expander("Why paste manually?"):
                st.markdown("""
Investment options can't be reliably extracted from Excel because:
- They're often formulas like `=A1`
- Cells are merged or inconsistently placed
- No clear pattern to find them automatically

To avoid errors, paste one option per line in the same order as the fund names.
""")
            investment_input = st.text_area("Paste Investment Options", "", height=180)
            investment_options = [o.strip() for o in investment_input.splitlines() if o.strip()]
            if any(o.startswith("=") for o in investment_options):
                st.warning("Looks like a formula — paste plain text only.")

        if fund_names and investment_options:
            st.caption("Preview Match")
            if len(fund_names) != len(investment_options):
                st.error("Mismatch: Fund and option counts don't match.")
                preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Closest Match": [max(investment_options, key=lambda opt: similar(f, opt)) for f in fund_names]
                })
            else:
                preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Investment Option": investment_options
                })
            st.dataframe(preview, use_container_width=True)

    # --- Step 4: Generate Output ---
    st.subheader("4. Generate Output")
    dry_run = st.checkbox("Dry Run (Preview Only — no file updated)", value=True)

    if st.button("🚀 Generate Scorecard"):
        if len(fund_names) != len(investment_options):
            st.error("Mismatch between fund names and options.")
            return

        try:
            progress = st.progress(0)
            with st.spinner("Working on it..."):
                progress.progress(30)
                result = update_excel_with_template(
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
                progress.progress(90)
                st.success("✅ Preview ready!" if dry_run else "✅ Excel updated!")

                st.dataframe(result, use_container_width=True)
                if not dry_run:
                    st.download_button(
                        "📥 Download Updated Excel",
                        data=result.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                progress.progress(100)
        except Exception as e:
            st.error("Something went wrong during generation.")
            st.exception(e)
