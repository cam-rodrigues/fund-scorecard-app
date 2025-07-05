import streamlit as st
from datetime import datetime

# ======================
#   PAGE CONFIG
# ======================
st.set_page_config(page_title="FidSync", layout="wide")

# ======================
#   SIDEBAR
# ======================
st.sidebar.title("FidSync")
st.sidebar.markdown("---")

# Navigation
st.sidebar.subheader("Navigate")
page = st.sidebar.radio("", ["About FidSync", "How to Use", "Fund Scorecard"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption(f"Version 1.1 • Updated {datetime.today().strftime('%b %d, %Y')}")

# ======================
#   PAGE ROUTING
# ======================
if page == "About FidSync":
    st.title("About FidSync")
    st.write("""
    FidSync is a modern web tool designed to streamline investment documentation workflows.

    **Current capabilities:**
    - Extract fund statuses from scorecard PDFs
    - Automate Excel status updates with smart matching

    **Coming soon:**
    - Compliance & audit support
    - Plan comparisons
    - Centralized audit logging
    """)
    
elif page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
    **Step-by-step:**

    1. Go to the **Fund Scorecard** tab.
    2. Upload a PDF fund report and your Excel workbook.
    3. Enter settings (sheet name, row, column).
    4. Paste in investment names (one per line).
    5. Click **Run Status Update** to extract and match.

    ✅ *Dry Run* mode lets you preview results before updating Excel.
    """)

elif page == "Fund Scorecard":
    from pages.fund_scorecard import render_scorecard_tool
    render_scorecard_tool()
