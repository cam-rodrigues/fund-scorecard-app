import streamlit as st
import pandas as pd

from utils.excel_utils import update_excel_with_template
from utils.pdf_utils import extract_data_from_pdf



def run():
    st.header("📊 Fund Scorecard")
    st.markdown("Upload an investment PDF and update the corresponding Excel scorecard with one click.")

    with st.expander("🔍 Upload Files", expanded=True):
        pdf_file = st.file_uploader("Upload Fund PDF", type=["pdf"])
        excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])

    if st.button("Generate Scorecard"):
        if not pdf_file or not excel_file:
            st.warning("Please upload both a PDF and Excel file.")
            return

        with st.spinner("Extracting and syncing data..."):
            try:
                pdf_data = extract_data_from_pdf(pdf_file)
                updated_df = update_excel_with_template(excel_file, pdf_data)

                st.success("✅ Scorecard updated successfully!")
                st.dataframe(updated_df, use_container_width=True)

                st.download_button(
                    label="⬇️ Download Updated Excel",
                    data=updated_df.to_excel(index=False, engine='openpyxl'),
                    file_name="updated_scorecard.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error("❌ Something went wrong while processing the files.")
                st.exception(e)
