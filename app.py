import streamlit as st
import importlib

# --- Page Setup ---
st.set_page_config(page_title="FidSync", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.markdown("## FidSync")
    st.caption("Built for clarity, trust, and automation.")

    page = st.selectbox(
        "Navigation",
        options=["About FidSync", "How to Use", "Fund Scorecard"]
    )

    st.markdown("---")
    st.caption("© 2025 FidSync Technologies")

# --- Page Routing ---
page_modules = {
    "About FidSync": "app_pages.About_FidSync",
    "How to Use": "app_pages.How_to_Use",
    "Fund Scorecard": "app_pages.fund_scorecard"
}

try:
    mod = importlib.import_module(page_modules[page])
    mod.run()
except Exception as e:
    st.error(f"Error loading page '{page}': {e}")
