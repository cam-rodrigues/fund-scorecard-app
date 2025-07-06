import streamlit as st

def run():
    st.title("📖 How to Use FidSync")

    st.markdown("""
    Follow these 3 simple steps to update your fund scorecard:

    ### 1️⃣ Upload Your Files
    - **PDF Report**: This is usually a fund report like MPI or other investment research.
    - **Excel Template**: Your formatted workbook that will receive the updated Pass/Fail statuses.

    ### 2️⃣ Set Page Range
    - Select the **start** and **end** page numbers from the PDF where the fund names appear.

    ### 3️⃣ Input Investment Options
    - You can either:
        - **Paste** one option per line
        - **Upload** a simple CSV with a single column
    - These should be in the same order as the fund names in the PDF.

    ---
    After clicking **"Run Scorecard"**, you'll be able to:
    - Preview the matches
    - Download the updated Excel file with Pass/Fail flags

    ---
    ⚠️ **Important Notes**
    - The tool does not extract investment options from Excel or PDF automatically.
    - This is because investment options are often in formulas, inconsistent layouts, or scattered cells.
    - That’s why you need to input or upload them manually — once per run.

    ---
    Need help? Reach out to the FidSync team or submit a request on the "User Requests" tab (coming soon).
    """)
