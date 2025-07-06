import streamlit as st

def run():
    st.title("📖 How to Use FidSync")

    st.markdown("""
    Follow these 3 simple steps to update your fund scorecard:

    ---
    ### 1️⃣ Upload Your Files
    - **PDF Report** (e.g., MPI, Callan, Mercer): Contains fund names.
    - **Excel Template**: Your customized workbook where Pass/Fail logic will be applied.

    ---
    ### 2️⃣ Set the Page Range
    - Choose the **start** and **end** pages from your PDF where fund names appear.

    ---
    ### 3️⃣ Provide Investment Options
    You must supply the investment options manually:
    - ✍️ **Paste**: One per line
    - 📁 **Upload**: A CSV with a single column

    These should follow the **same order** as the extracted fund names.

    ---
    After clicking **“🚀 Run Scorecard”**, you’ll be able to:
    - ✅ Preview the fund–option pairs
    - 📥 Download your updated Excel file

    ---
    ⚠️ **Important**
    - Investment options **cannot** be extracted automatically from Excel or PDF.
    - This is due to inconsistent formatting: formulas, merged cells, or scattered layouts.
    - You must input or upload them **manually each time**.

    ---
    📬 Need help? Reach out to the FidSync team or submit feedback (feature coming soon).
    """)
