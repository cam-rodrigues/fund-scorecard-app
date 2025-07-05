import streamlit as st
from datetime import datetime
from pages.fund_scorecard import render_scorecard_tool

st.set_page_config(page_title="FidSync", layout="wide")

# Sidebar Layout
st.sidebar.title("FidSync")
st.sidebar.markdown("---")
st.sidebar.subheader("Navigate")
page = st.sidebar.radio("", ["About FidSync", "How to Use", "Fund Scorecard"], label_visibility="collapsed")

st.sidebar.caption(f"Version 1.1 • Updated {datetime.today().strftime('%b %d, %Y')}")

# Route to page
if page == "About FidSync":
    st.title("About FidSync")
    st.markdown("""
FidSync is a lightweight, secure platform for streamlining fund documentation workflows.
It enables fast and accurate parsing of investment reports, efficient Excel updates, and is
designed to scale with future tools for compliance, audits, and plan comparisons.

**Current Capabilities:**
- Fund Scorecard Parsing
- Excel Status Updating

**Coming Soon:**
- Compliance Checks
- Audit Log Tracking
- Plan Comparisons
    """)

elif page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
**Step-by-Step Instructions:**
1. Upload a Fund Scorecard PDF.
2. Upload the Excel workbook.
3. Specify the sheet name, starting row number, and starting column.
4. Paste in a list of investment option names.
5. Click **Run Status Update** to extract and match.
6. Download the updated Excel and optional match log.

**Tips:**
- PDF pages match the printed page numbers.
- Use the Dry Run checkbox to test matches before writing anything to Excel.
""")

elif page == "Fund Scorecard":
    render_scorecard_tool()
