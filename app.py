import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(page_title="FidSync", layout="wide")

# Sidebar navigation
st.sidebar.title("FidSync")
st.sidebar.markdown("---")
st.sidebar.subheader("Navigate")
page = st.sidebar.radio("", ["About FidSync", "How to Use", "Fund Scorecard"], label_visibility="collapsed")

if page == "About FidSync":
    st.title("About FidSync")
    st.markdown("""
    FidSync is a lightweight, modular web tool for fiduciary compliance support.  
    - Built for accuracy, clarity, and speed.  
    - Designed to scale with your workflow.  
    - Future tools include plan comparison, audit trails, and compliance verification.
    """)

elif page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
    #### Step-by-step:
    1. Upload your Fund Scorecard PDF and Excel workbook.
    2. Enter the sheet name, starting row number, and status column.
    3. Paste investment names, one per line.
    4. Click **Run Status Update** to extract and match.
    5. Download your updated file and logs.

    ✅ **Dry Run**: Check the match results before making real changes.  
    ✅ **Live Mode**: Updates the Excel directly with color-coded statuses.
    """)

elif page == "Fund Scorecard":
    from pages.fund_scorecard import show
    show()

