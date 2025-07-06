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

    # --- Full Help Section ---
    with st.expander("📘 How to Use This Tool", expanded=False):
        st.markdown("""
The Fund Scorecard lets you:
- Extract fund names from a PDF
- Manually or automatically match them to investment options
- Update your Excel template with a pass/fail status

**Why investment options can’t be extracted from Excel:**
- They’re often formulas (`=A1`) instead of text
- The layout is inconsistent (merged cells, scattered rows)
- Headers may be missing

So you’ll need to paste investment options manually — one per line in the same order as the funds.
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

        # Extract fund names from PDF
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text_lines = []
                pages = pdf.pages[start_page - 1:end_page]
                for page in pages:
                    text = page.extract_text()
                    if text:
                        text_lines += [line.strip() for line in text.split("\n") if "fund" in line.lower()]

                fund_names = sorted(set(text_lines))

            st.caption(f"Extracted {len(fund_names)} fund name(s) from the PDF.")

            show_funds = st.checkbox("Show/Edit Extracted Fund Names", value=True)
            if show_funds:
                fund_text = st.text_area("Fund Names", value="\n".join(fund_names), height=200)
                fund_names = [line.strip() for line in fund_text.splitlines() if line.strip()]

        except Exception as e:
            st.error("Failed to extract fund names from the PDF.")
            st.exception(e)
            return

        # Investment Options Input
        st.markdown("### Provide Investment Options")
        method = st.radio("Choose Input Method", ["Paste Manually", "Upload CSV"], horizontal=True)

        investment_options = []

        if method == "Upload CSV":
            csv_file = st.file_uploader("Upload CSV File", type="csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    col = st.selectbox("Select Column", df.columns)
                    investment_options = df[col].dropna().astype(str).tolist()
                    st.success(f"Loaded {len(investment_options)} investment options from CSV.")
                except Exception as e:
                    st.error("Error reading the CSV file.")
                    st.exception(e)
        else:
            with st.expander("Why do I have to paste these manually?"):
                st.markdown("""
Investment options can’t be auto-extracted from Excel because:
- They’re stored as **formulas** (e.g. `=A1`)
- Layouts vary too much
- Headers and cell formatting aren't consistent

Please paste them one per line in order.
""")

            options_text = st.text_area("Paste Investment Options", "", height=200, help="One per line, in the same order as fund names.")
            investment_options = [line.strip() for line in options_text.splitlines() if line.strip()]
            if any(line.startswith("=") for line in investment_options):
                st.warning("Some lines look like formulas. Paste plain text only.")

        # --- Preview Match ---
        if fund_names and investment_options:
            st.markdown("### Match Preview")

            if len(fund_names) != len(investment_options):
                st.error(f"⚠️ Fund and option counts don’t match ({len(fund_names)} vs {len(investment_options)}).")
                st.caption("We’ll show the closest match guesses below:")

                preview_df = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Closest Match": [
                        max(investment_options, key=lambda opt: similar(fund, opt))
                        for fund in fund_names
                    ]
                })
                st.dataframe(preview_df, use_container_width=True)
            else:
                preview_df = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Investment Option": investment_options
                })
                st.dataframe(preview_df, use_container_width=True)

    # --- Step 4: Generate ---
    dry_run = st.checkbox("Dry Run (Preview Only)", value=True)

    if st.button("Generate Scorecard"):
        if len(fund_names) != len(investment_options):
            st.error("Line mismatch — make sure every fund has one matching investment option.")
            return

        try:
            with st.spinner("Processing your files..."):
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
                st.success("✅ Done!")
                st.dataframe(result_df)

                if not dry_run:
                    st.download_button(
                        "Download Updated Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error("Something went wrong.")
            st.exception(e)
