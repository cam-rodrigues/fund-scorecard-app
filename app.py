import streamlit as st
from app_pages import fund_scorecard, user_requests

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FidSync | Fund Management Platform",
    page_icon="📊",
    layout="wide"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📁 FidSync")
st.sidebar.markdown("Automated fund tools for wealth advisors.")

page = st.sidebar.radio(
    "Navigate to:",
    options=["Fund Scorecard", "User Requests"],
    key="selected_page"
)

# --- MAIN CONTENT AREA ---
st.title("FidSync Platform")
st.markdown("Welcome to FidSync, your internal toolkit for syncing fund data, reports, and client requests.")

if page == "Fund Scorecard":
    fund_scorecard.run()
elif page == "User Requests":
    user_requests.run()
