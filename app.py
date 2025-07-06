import streamlit as st
import importlib

# --- Sidebar Branding ---
st.set_page_config(page_title="FidSync", layout="wide")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Sync_icon.svg/1200px-Sync_icon.svg.png", width=80)
    st.markdown("### FidSync")
    page = st.selectbox(
        "Navigate",
        ("Fund Scorecard", "How to Use", "About FidSync")
    )
    st.markdown("---")
    st.markdown("Built for clarity, trust, and automation.")

# --- Dynamic Page Loader ---
page_modules = {
    "Fund Scorecard": "app_pages.fund_scorecard",
    "How to Use": "app_pages.How to Use",
    "About FidSync": "app_pages.About FidSync"
}

try:
    mod = importlib.import_module(page_modules[page])
    mod.run()
except Exception as e:
    st.error(f"Error loading page '{page}': {e}")
