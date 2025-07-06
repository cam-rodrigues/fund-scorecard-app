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
    st.title("FidSync: Fund Scorecard")
    st.markdown("Easily match fund names from PDF reports with investment options, then update Excel templates.")
    st.markdown("---")

    # --- Help Section ---
    with st.expander("📘 How It Works", expanded=False):
        st.markdown("""
**This tool lets you:**
- Pull fund names from a PDF (30–40 pages)
- Manually paste matching investment options
- Insert results into an Excel template

**Why manual paste?**
Investment options in Excel are often:
- Formulas (like `=A1`)  
- In inconsistent locations or merged cells  
- Missing clear headers  

To avoid mistakes, paste them manually — one per line.
""")

    # --- Step 1: Upload Files ---
    with st.container():
        st.subheader("Step 1: Upload Files")
        pdf_file = st.file_uploader("PDF Report", type=["pdf"])
        excel_file = st.file_uploader("Excel Template", type=["xlsx"])
        if not pdf_file or not excel_file:
            st.info("Upload both a PDF and Excel file to continue.")
            return

    # --- Step 2: Configuration ---
    with st.container():
        st.subheader("Step 2: Configure Settings")
        sheet_name = st.text_input("Excel Sheet Name")
        col1, col2 = st.columns(2)
        with col1:
            start_col = st.text_input("Start Column (A–Z)", max_chars=1).upper().strip()
            if start_col and (not start_col.isalpha() or len(start_col) != 1):
                st.warning("Start Column must be a single letter.")
                return
        with col2:
            start_row = st.number_input("Start Row (e.g. 2)", min_value=1, step=1)

        col3, col4 = st.columns(2)
        with col3:
            start_page = st.number_input("PDF Start Page", min_value=1, step=1)
        with col4:
            end_page = st.number_input("PDF End Page", min_value=1, step=1)

    # --- Step 3: Extract Fund Names ---
    with st.container():
        st.subheader("Step 3: Extract Fund Names from PDF")
        fund_names = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                pages = pdf.pages[start_page - 1:end_page]
                lines = []
                for p in pages:
                    text = p.extract_text()
                    if text:
                        lines += [l.strip() for l in text.split("\n") if "fund" in l.lower()]
                fund_names = sorted(set(lines))

            st.success(f"{len(fund_names)} fund name(s) found.")
            if st.checkbox("Edit Fund Names", value=False):
                edited = st.text_area("Fund Names", "\n".join(fund_names), height=200)
                fund_names = [f.strip() for f in edited.splitlines() if f.strip()]
        except Exception as e:
            st.error("Error reading PDF.")
            st.exception(e)
            return

    # --- Step 4: Provide Investment Options ---
    with st.container():
        st.subheader("Step 4: Provide Investment Options")
        method = st.radio("Choose input method", ["Paste Manually", "Upload CSV"], horizontal=True)
        investment_options = []

        if method == "Upload CSV":
            csv_file = st.file_uploader("Upload CSV File", type="csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    col = st.selectbox("Column with Investment Options", df.columns)
                    investment_options = df[col].dropna().astype(str).tolist()
                    st.success(f"{len(investment_options)} options loaded.")
                except Exception as e:
                    st.error("CSV loading failed.")
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
            options_text = st.text_area("Paste One Option Per Line", "", height=200)
            investment_options = [o.strip() for o in options_text.splitlines() if o.strip()]
            if any(line.startswith("=") for line in investment_options):
                st.warning("Looks like you're pasting formulas. Please paste plain text.")

    # --- Step 5: Preview Match ---
    if fund_names and investment_options:
        with st.container():
            st.subheader("Step 5: Preview Matches")
            if len(fund_names) != len(investment_options):
                st.error(f"Mismatch: {len(fund_names)} fund names vs {len(investment_options)} options.")
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

    # --- Step 6: Generate Output ---
    with st.container():
        st.subheader("Step 6: Generate Scorecard")
        dry_run = st.checkbox("Dry Run (Preview Only)", value=True)

        if st.button("Generate Scorecard"):
            if len(fund_names) != len(investment_options):
                st.error("Line count mismatch.")
                return

            try:
                progress = st.progress(0)
                with st.spinner("Generating..."):
                    progress.progress(25)
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
                    progress.progress(85)
                    st.success("✅ Done!" if not dry_run else "✅ Preview ready.")
                    st.dataframe(result)
                    if not dry_run:
                        st.download_button(
                            "Download Updated Excel",
                            data=result.to_excel(index=False, engine="openpyxl"),
                            file_name="updated_scorecard.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    progress.progress(100)
            except Exception as e:
                st.error("Something went wrong.")
                st.exception(e)
