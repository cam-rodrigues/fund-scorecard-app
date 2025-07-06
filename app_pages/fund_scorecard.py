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
    st.header("Fund Scorecard")

    # --- Help Section ---
    with st.expander("📘 How to Use This Tool", expanded=False):
        st.markdown("""
This tool helps you:
- Extract fund names from a PDF
- Match them to investment options (manually or from CSV)
- Update an Excel template with pass/fail results

You'll upload files, configure where to write data, and paste or upload the investment option names.
""")

    # --- Step 1: Upload Files ---
    with st.expander("Step 1: Upload PDF + Excel", expanded=True):
        st.caption("Upload the PDF with fund names and the Excel template to update.")
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("Upload PDF Report", type=["pdf"])
        with col2:
            excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    if not pdf_file or not excel_file:
        st.info("Please upload both a PDF and an Excel file to continue.")
        return

    # --- Step 2: Configure Excel Settings ---
    with st.expander("Step 2: Set Excel + PDF Page Parameters", expanded=True):
        st.caption("Tell the app where to write and what page range to scan.")

        sheet_name = st.text_input("Excel Sheet Name", help="The name of the sheet/tab to update.")
        start_col = st.text_input("Start Column (e.g. 'B')", max_chars=1, help="One letter only, where the 'Start' or 'Pass/Fail' column begins.").upper().strip()
        start_row = st.number_input("Start Row", min_value=1, help="This is usually 2 if row 1 is your header.")
        start_page = st.number_input("PDF Start Page", min_value=1, help="First page to extract fund names from.")
        end_page = st.number_input("PDF End Page", min_value=1, help="Last page to extract fund names from.")

        if start_col and (not start_col.isalpha() or len(start_col) != 1):
            st.warning("Start Column must be a single letter from A to Z.")
            return

    # --- Step 3: Fund Names + Investment Options ---
    with st.expander("Step 3: Match Fund Names to Investment Options", expanded=True):
        fund_names = []

        try:
            with pdfplumber.open(pdf_file) as pdf:
                text_lines = []
                pages = pdf.pages[start_page - 1:end_page]
                for page in pages:
                    text = page.extract_text()
                    if text:
                        text_lines += [line.strip() for line in text.split("\n") if "fund" in line.lower()]
                fund_names = sorted(set(text_lines))

            st.caption(f"✅ Extracted {len(fund_names)} fund name(s) from PDF.")
            if st.checkbox("Show/edit fund names", value=True):
                fund_text = st.text_area("Fund Names (edit if needed)", value="\n".join(fund_names), height=200)
                fund_names = [line.strip() for line in fund_text.splitlines() if line.strip()]

        except Exception as e:
            st.error("Failed to extract fund names from PDF.")
            st.exception(e)
            return

        # Investment Options Input
        st.caption("Provide Investment Options")
        method = st.radio("", ["Paste Manually", "Upload CSV"], horizontal=True, label_visibility="collapsed")

        investment_options = []

        if method == "Upload CSV":
            csv_file = st.file_uploader("Upload CSV File", type="csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    col = st.selectbox("Choose column with investment options", df.columns)
                    investment_options = df[col].dropna().astype(str).tolist()
                    st.success(f"Loaded {len(investment_options)} investment options from CSV.")
                except Exception as e:
                    st.error("Could not read CSV.")
                    st.exception(e)
        else:
            with st.expander("Why do I have to paste these manually?"):
                st.markdown("""
Investment options can’t be pulled from Excel because:
- They're often stored as **formulas** (like `=A1`)
- Layouts vary, cells may be merged or headers missing

So paste them here, one per line, in the same order as fund names.
""")
            options_text = st.text_area("Paste Investment Options", "", height=200, help="One per line.")
            investment_options = [line.strip() for line in options_text.splitlines() if line.strip()]
            if any(line.startswith("=") for line in investment_options):
                st.warning("Some lines look like formulas. Paste plain text only.")

        # Preview
        if fund_names and investment_options:
            st.caption("Preview Match")
            if len(fund_names) != len(investment_options):
                st.error(f"⚠️ Fund and option counts don’t match ({len(fund_names)} vs {len(investment_options)}).")
                preview_df = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Closest Match": [
                        max(investment_options, key=lambda opt: similar(fund, opt))
                        for fund in fund_names
                    ]
                })
            else:
                preview_df = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Investment Option": investment_options
                })
            st.dataframe(preview_df, use_container_width=True)

    # --- Step 4: Generate ---
    dry_run = st.checkbox("Preview Only (Dry Run) — disables download", value=True)

    if st.button("Generate Scorecard"):
        if len(fund_names) != len(investment_options):
            st.error("Fund name and option counts must match.")
            return

        try:
            progress = st.progress(0)
            with st.spinner("Processing..."):
                progress.progress(30)
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
                progress.progress(90)
                st.success("✅ Preview generated successfully (no file created)." if dry_run else "✅ File updated successfully.")
                st.dataframe(result_df)
                if not dry_run:
                    progress.progress(100)
                    st.download_button(
                        "Download Updated Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error("Something went wrong.")
            st.exception(e)
