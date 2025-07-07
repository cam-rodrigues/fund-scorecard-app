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
    st.markdown("## FidSync: Fund Scorecard")

    with st.expander("Instructions"):
        st.markdown("""
        1. Upload your **PDF fund scorecard** and **Excel file**.
        2. Paste in your **investment options** (one per line).
        3. Click **Run** to process and match fund names.
        4. Sort, filter, or tweak the results directly in the table.
        5. Download your updated Excel or CSV file.
        """)

    with st.expander("Tips & Notes"):
        st.markdown("""
        - Investment options must be pasted manually due to Excel formatting (formulas, merged cells, etc.).
        - Paste in plain text only.
        - Matching is done with smart fuzzy logic — double-check results if needed.
        """)

    # --- File Uploads ---
    st.markdown("### Upload Files")
    col1, col2 = st.columns(2)

    with col1:
        pdf_file = st.file_uploader("Upload PDF Fund Scorecard", type=["pdf"])

    with col2:
        excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    # --- Investment Options Input ---
    st.markdown("### Provide Investment Options")
    investment_input = st.text_area(
        "Paste investment options here (one per line):",
        height=200,
        placeholder="Large Cap Equity Fund\nSmall Cap Growth\nMid Cap Value\n..."
    )

    if st.button("Run"):
        if not pdf_file or not excel_file or not investment_input.strip():
            st.error("Please upload both files and provide investment options.")
            return

        with st.spinner("Processing..."):
            # Extract fund statuses from PDF
            try:
                fund_statuses = extract_data_from_pdf(pdf_file)
            except Exception as e:
                st.error(f"Failed to read PDF: {e}")
                return

            investment_options = [line.strip() for line in investment_input.strip().splitlines() if line.strip()]
            matched_funds = []

            # Match investment options to fund statuses using fuzzy matching
            for option in investment_options:
                best_match = max(fund_statuses.items(), key=lambda x: similar(option, x[0]), default=None)
                matched_funds.append((option, best_match[1] if best_match else "Not Found"))

            # Display filterable, editable table
            st.markdown("### 🔍 Match Preview (Editable)")
            preview_df = pd.DataFrame(matched_funds, columns=["Investment Option", "Fund Status"])
            editable_df = st.data_editor(
                preview_df,
                use_container_width=True,
                num_rows="fixed",
                hide_index=True,
                key="editable_table"
            )

            # Download CSV
            csv_data = editable_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 Download Results as CSV",
                data=csv_data,
                file_name="fund_scorecard_results.csv",
                mime="text/csv"
            )

            # Update Excel
            try:
                updated_excel = update_excel_with_template(excel_file, editable_df.values.tolist())
                st.success("✅ Excel updated successfully!")
                st.download_button("📥 Download Updated Excel", data=updated_excel, file_name="updated_funds.xlsx")
            except Exception as e:
                st.error(f"Error updating Excel: {e}")
