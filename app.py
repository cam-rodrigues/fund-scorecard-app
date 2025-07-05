# app.py
import streamlit as st
from datetime import datetime

# ======================
# Page Config
# ======================
st.set_page_config(page_title="FidSync", layout="wide")

# ======================
# Sidebar Navigation
# ======================
st.sidebar.title("FidSync")
st.sidebar.markdown("---")
st.sidebar.subheader("Navigate")
page = st.sidebar.radio("", ["About FidSync", "How to Use", "Fund Scorecard"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.subheader("Tools")
st.sidebar.caption(f"Version 1.1 • Updated {datetime.today().strftime('%b %d, %Y')}")

# ======================
# Page Routing
# ======================
if page == "About FidSync":
    st.title("About FidSync")
    st.markdown("""
FidSync is a scalable, secure platform for financial documentation automation.  
Initially designed for Fund Scorecard processing, it is growing to include:

- ✅ Scorecard Parsing  
- ✅ Excel Updates  
- 🔒 Compliance Checks (Coming Soon)  
- 📊 Plan Comparisons  
- 🕵️‍♂️ Audit Logging  
    """)
elif page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
**Step-by-Step Guide**  
1. Upload your Fund Scorecard PDF and the target Excel workbook.  
2. Provide the sheet name, starting row, and column where statuses should go.  
3. Paste your list of investment options (one per line).  
4. Click **Run Status Update** to process and download the results.

Use **Dry Run** to preview results without modifying the Excel file.
    """)
elif page == "Fund Scorecard":
    from pages.fund_scorecard import render_fund_scorecard
    render_fund_scorecard()
