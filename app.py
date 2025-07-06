import streamlit as st
import importlib

# --- Page Setup ---
st.set_page_config(page_title="FidSync", page_icon="🔄", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Sync_icon.svg/1200px-Sync_icon.svg.png", width=80)
    st.markdown("## FidSync")
    
    # Ordered navigation
    page = st.selectbox(
        "📂 Navigate",
        options=["About FidSync", "How to Use", "Fund Scorecard"]
    )

    st.markdown("---")
    st.markdown("Built for clarity, trust, and automation.")

# --- Page Routing ---
page_modules = {
    "About FidSync": "app_pages.About_FidSync",
    "How to Use": "app_pages.How_to_Use",
    "Fund Scorecard": "app_pages.fund_scorecard"
}

try:
    module_name = page_modules[page]
    mod = importlib.import_module(module_name)
    mod.run()
except Exception as e:
    st.error(f"🚨 Error loading '{page}': {e}")
