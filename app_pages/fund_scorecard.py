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
    st.title("FidSync Fund Scorecard")
    st.markdown(
        "A clean, accurate way to extract fund names from PDF reports, align them with investment options, and update your Excel templates — no Excel hacks required."
    )
    st.divider()

    # ───────────────────────────────────────────────────────────────────────────────
    # HELP SECTION
    # ───────────────────────────────────────────────────────────────────────────────
    with st.expander("ℹ️ How this tool works", expanded=False):
        st.markdown("""
This app performs 3 core tasks:
1. **Extracts fund names** from PDF reports (usually 30–40 pages)
2. **Lets you paste or upload matching investment options**
3. **Writes results** into a structured Excel scorecard

> **Why do I need to paste investment options?**  
They’re stored as **formulas** (e.g. `=A1`) and live in **merged** or **unpredictable cells** in Excel. That makes them hard to extract automatically.  
Instead, just paste them — one per line — in the same order as the funds.
""")

    # ───────────────────────────────────────────────────────────────────────────────
    # STEP 1: Upload Files
    # ───────────────────────────────────────────────────────────────────────────────
    with st.container():
        st.subheader("Step 1: Upload Files")
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("Upload PDF Report", type=["pdf"])
        with col2:
            excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

        if not pdf_file or not excel_file:
            st.info("Please upload both files to proceed.")
            return

    # ───────────────────────────────────────────────────────────────────────────────
    # STEP 2: Configure Excel and PDF Settings
    # ───────────────────────────────────────────────────────────────────────────────
    with st.container():
        st.subheader("Step 2: Configure Target Sheet")
        col1, col2, col3 = st.columns(3)
        with col1:
            sheet_name = st.text_input("Excel Sheet Name")
        with col2:
            start_col = st.text_input("Start Column (e.g. B)", max_chars=1).upper().strip()
            if start_col and (not start_col.isalpha() or len(start_col) != 1):
                st.warning("Start Column must be a single letter.")
                return
        with col3:
            start_row = st.number_input("Start Row", min_value=1, step=1)

        col4, col5 = st.columns(2)
        with col4:
            start_page = st.number_input("PDF Start Page", min_value=1, step=1)
        with col5:
            end_page = st.number_input("PDF End Page", min_value=1, step=1)

    # ───────────────────────────────────────────────────────────────────────────────
    # STEP 3: Extract Fund Names from PDF
    # ───────────────────────────────────────────────────────────────────────────────
    with st.container():
        st.subheader("Step 3: Extract Fund Names from PDF")
        fund_names = []

        try:
            with pdfplumber.open(pdf_file) as pdf:
                pages = pdf.pages[start_page - 1:end_page]
                for page in pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            if "fund" in line.lower() and len(line.strip()) < 80:
                                fund_names.append(line.strip())
            fund_names = sorted(set(fund_names))
            st.success(f"✅ {len(fund_names)} fund name(s) extracted.")

            if st.checkbox("Edit Extracted Fund Names"):
                raw_text = st.text_area("Fund Names", "\n".join(fund_names), height=180)
                fund_names = [line.strip() for line in raw_text.splitlines() if line.strip()]
        except Exception as e:
            st.error("Failed to extract text from PDF. Please check the page range.")
            st.exception(e)
            return

    # ───────────────────────────────────────────────────────────────────────────────
    # STEP 4: Add Investment Options
    # ───────────────────────────────────────────────────────────────────────────────
    with st.container():
        st.subheader("Step 4: Provide Matching Investment Options")

        input_mode = st.radio("Choose how to enter investment options:", ["Paste Manually", "Upload CSV"], horizontal=True)
        investment_options = []

        if input_mode == "Upload CSV":
            csv_file = st.file_uploader("Upload CSV with Investment Options", type="csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    selected_column = st.selectbox("Select Column Containing Options", df.columns)
                    investment_options = df[selected_column].dropna().astype(str).tolist()
                    st.success(f"{len(investment_options)} options loaded from CSV.")
                except Exception as e:
                    st.error("Error reading CSV.")
                    st.exception(e)
        else:
            with st.expander("Why manual paste?"):
                st.markdown("""
- Excel stores investment names as **formulas** (not text)
- Layout is inconsistent (merged or scattered cells)
- We can't reliably extract them automatically

✅ Just paste one investment option per line, in the same order as the funds.
""")
            pasted = st.text_area("Paste One Option Per Line", "", height=180)
            investment_options = [line.strip() for line in pasted.splitlines() if line.strip()]
            if any(line.startswith("=") for line in investment_options):
                st.warning("Looks like a formula — paste plain text instead.")

    # ───────────────────────────────────────────────────────────────────────────────
    # STEP 5: Preview Mapping
    # ───────────────────────────────────────────────────────────────────────────────
    if fund_names and investment_options:
        with st.container():
            st.subheader("Step 5: Preview Fund Matches")
            if len(fund_names) != len(investment_options):
                st.error(f"Mismatch: {len(fund_names)} fund names vs {len(investment_options)} options.")
                preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Closest Match (Fuzzy)": [max(investment_options, key=lambda o: similar(f, o)) for f in fund_names]
                })
            else:
                preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Investment Option": investment_options
                })
            st.dataframe(preview, use_container_width=True)

    # ───────────────────────────────────────────────────────────────────────────────
    # STEP 6: Generate Scorecard
    # ───────────────────────────────────────────────────────────────────────────────
    with st.container():
        st.subheader("Step 6: Generate Scorecard")

        dry_run = st.checkbox("Dry Run (Preview only — does not modify Excel)", value=True)

        if st.button("Generate Scorecard"):
            if len(fund_names) != len(investment_options):
                st.error("Number of funds and options must match.")
                return

            try:
                progress = st.progress(0)
                with st.spinner("Working..."):
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
                    st.success("✅ Scorecard ready!" if not dry_run else "✅ Preview complete.")
                    st.dataframe(result_df)

                    if not dry_run:
                        st.download_button(
                            label="📥 Download Updated Excel",
                            data=result_df.to_excel(index=False, engine="openpyxl"),
                            file_name="updated_scorecard.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    progress.progress(100)
            except Exception as e:
                st.error("Something went wrong.")
                st.exception(e)
