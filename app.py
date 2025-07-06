import streamlit as st
import importlib

# --- Page Setup ---
st.set_page_config(page_title="FidSync", layout="wide")

# --- Sidebar Layout ---
with st.sidebar:
    # Use your logo — you can replace this URL with your hosted PNG if needed
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Sync_icon.svg/1200px-Sync_icon.svg.png", width=80)
    st.markdown("### FidSync")
    
    page = st.selectbox(
        "Navigate",
        ("About FidSync", "How to Use", "Fund Scorecard")
    )

    st.markdown("---")
    st.markdown("Built for clarity, trust, and automation.")

# --- Dynamic Page Loading ---
page_modules = {
    "About FidSync": "app_pages.About FidSync",
    "How to Use": "app_pages.How to Use",
    "Fund Scorecard": "app_pages.fund_scorecard"
}

try:
    mod = importlib.import_module(page_modules[page])
    mod.run()
except Exception as e:
    st.error(f"Error loading page '{page}': {e}")
