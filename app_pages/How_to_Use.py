import streamlit as st

def run():
    st.title("How to Use FidSync")

    st.markdown("""
    ### Step-by-Step Guide

    **1. Upload Your Files**
    - Upload your PDF report (e.g., MPI, Mercer)
    - Upload your Excel workbook for scorecard updates

    **2. Select Page Range**
    - Choose the page numbers from the PDF where fund names appear

    **3. Input Investment Options**
    - Paste one option per line _or_ upload a CSV with a single column
    - Ensure the order matches the funds extracted

    **4. Run the Scorecard**
    - Review matched results
    - Download your updated Excel workbook

    ---
    ### Important Notes
    - Investment options cannot be auto-extracted due to layout inconsistencies in Excel/PDFs
    - You must manually input or upload them in the correct order for each session
    """)
