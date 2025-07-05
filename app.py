import streamlit as st
from app_pages import fund_scorecard, user_requests

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FidSync",
    layout="wide"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("FidSync")

# First group: help pages
st.sidebar.markdown("**Info**")
info_page = st.sidebar.radio(
    "",
    options=["About", "How to Use"],
    index=0,
    key="info_page"
)

# Divider
st.sidebar.markdown("---")

# Second group: tools
st.sidebar.markdown("**Tools**")
tool_page = st.sidebar.radio(
    "",
    options=["Fund Scorecard", "User Requests"],
    index=0,
    key="tool_page"
)

# --- PAGE ROUTING ---
if info_page == "About":
    st.title("About FidSync")
    st.markdown("""
FidSync is an internal platform built to help wealth advisors extract, organize, and sync fund data quickly and reliably.  
It automates scorecard updates, streamlines audits, and reduces manual tracking effort.
""")

elif info_page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
**Fund Scorecard Tool**
- Upload the relevant PDF and Excel files
- Enter configuration options (sheet name, column, row, page range)
- Click "Generate Scorecard" to extract and apply fund statuses
- Download the updated Excel file

**User Requests**
- Use this form to suggest a new tool or improvement
""")

elif tool_page == "Fund Scorecard":
    fund_scorecard.run()

elif tool_page == "User Requests":
    user_requests.run()
