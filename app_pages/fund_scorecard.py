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

    with st.expander("📘 How to Use the Fund Scorecard Tool", expanded=False):
        st.markdown("""
The Fund Scorecard helps you sync fund names from PDF reports with investment options in Excel templates — used for compliance or reporting.

---

### 1. Upload Required Files
You must upload:
- 📄 A **PDF** fund report (30–40 pages)
- 📊 An **Excel** template to update

---

### 2. Configure Matching Parameters
Set:
- **Sheet Name**: Which Excel tab to update  
- **Start Column**: Where to write 'Start' values (e.g., B)  
- **Start Row**: Which row contains the first data  
- **PDF Page Range**: Pages to extract fund names from

---

### 3. Match Fund Names with Investment Options

📄 Fund names are pulled from the PDF.  
📋 Investment options must be **pasted manually** or uploaded via CSV.

> Why can't the app read investment options from Excel?
- They're often stored as formulas (`=A1`)
- Layouts are inconsistent
- Merged cells or missing headers break detection

Paste **one per line** in the same order as the fund names.

---

### Mismatch Preview
If your fund name and investment option counts differ:
- You'll see a warning
- We'll show the **closest matching guesses** to help troubleshoot

---

### Dry Run Mode
Use this to preview changes before updating Excel.

---

### Download Result
If the preview looks good, hit **Generate**.  
You’ll get a download link to your updated Excel scorecard.
        """)


    # --- Upload Files ---
    with st.expander("1. Upload Required Files", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("Upload PDF Report", type=["pdf"])
        with col2:
            excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    if not pdf_file or not excel_file:
        st.info("Both a PDF and Excel file are required to proceed.")
        return

    # --- Configure Settings ---
    with st.expander("2. Configure Matching Parameters", expanded=True):
        sheet_name = st.text_input("Excel Sheet Name")
        start_col = st.text_input("Start Column (e.g. 'B')", max_chars=1).upper().strip()
        start_row = st.number_input("Start Row (first row of data)", min_value=1)
        start_page = st.number_input("PDF Start Page", min_value=1)
        end_page = st.number_input("PDF End Page", min_value=1)

        if start_col and (not start_col.isalpha() or len(start_col) != 1):
            st.warning("Please use a single-letter column reference (A-Z).")
            return

    # --- Step 3: Match Fund Names and Investment Options ---
    with st.expander("3. Match Fund Names with Investment Options", expanded=True):
        fund_names = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                pages = pdf.pages[start_page - 1:end_page]
                lines = []
                for page in pages:
                    text = page.extract_text()
                    if text:
                        lines.extend([line.strip() for line in text.split("\n") if "fund" in line.lower()])
                fund_names = sorted(set(lines))

            show_raw = st.checkbox("Show/Edit Extracted Fund Names", value=True)
            if show_raw:
                fund_text = st.text_area("Extracted Fund Names", value="\n".join(fund_names), height=200)
                fund_names = [line.strip() for line in fund_text.splitlines() if line.strip()]
            st.caption(f"📄 {len(fund_names)} fund names listed")

        except Exception as e:
            st.error("Unable to extract fund names from the selected PDF pages.")
            st.exception(e)
            return

        st.markdown("### 📋 Provide Matching Investment Options")
        input_method = st.radio("Input Method", ["Paste Manually", "Upload CSV"], horizontal=True)

        investment_options = []
        if input_method == "Upload CSV":
            csv = st.file_uploader("Upload Investment Options CSV", type="csv")
            if csv:
                try:
                    df = pd.read_csv(csv)
                    col = st.selectbox("Select Column", df.columns)
                    investment_options = df[col].dropna().astype(str).tolist()
                    st.success(f"Loaded {len(investment_options)} investment options.")
                except Exception as e:
                    st.error("CSV could not be read.")
                    st.exception(e)
        else:
            with st.expander("Why do I have to paste these manually?"):
                st.markdown("""
Investment option names can’t be automatically pulled from Excel templates because:
- They're often stored as **formulas** (e.g., `=A1`)
- There’s no consistent layout or clear headers
- Merged cells break pattern detection

To ensure accuracy, paste each investment option manually — one per line.
                """)
            options_text = st.text_area("Paste Investment Options", "", height=200)
            investment_options = [line.strip() for line in options_text.splitlines() if line.strip()]
            if any(line.startswith("=") for line in investment_options):
                st.warning("⚠️ Some lines look like Excel formulas. Please paste plain text.")

        # --- Preview ---
        if fund_names and investment_options:
            st.markdown("### 🔍 Preview Match")
            if len(fund_names) != len(investment_options):
                st.error(f"Line mismatch: {len(fund_names)} fund names vs {len(investment_options)} investment options.")
                preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Closest Match (by text)": [
                        max(investment_options, key=lambda opt: similar(fund, opt))
                        for fund in fund_names
                    ]
                })
                st.dataframe(preview, use_container_width=True)
            else:
                preview = pd.DataFrame({
                    "Fund Name": fund_names,
                    "Investment Option": investment_options
                })
                st.dataframe(preview, use_container_width=True)

    dry_run = st.checkbox("Dry Run (Preview Only)", value=True)

    if st.button("Generate Scorecard"):
        if len(fund_names) != len(investment_options):
            st.error("The number of fund names and investment options must match.")
            return
        try:
            with st.spinner("Processing..."):
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
                st.success("Done!")
                st.dataframe(result_df)
                if not dry_run:
                    st.download_button(
                        "Download Updated Excel",
                        data=result_df.to_excel(index=False, engine="openpyxl"),
                        file_name="updated_scorecard.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error("Something went wrong while generating the scorecard.")
            st.exception(e)
