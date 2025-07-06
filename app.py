import streamlit as st
import importlib.util
import os

# === PAGE CONFIG ===
st.set_page_config(
    page_title="FidSync",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === LOGO + TITLE ===
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="https://i.imgur.com/VB0K4JG.png" alt="FidSync Logo" width="48"/>
        <h1 style="margin-bottom: 0;">FidSync</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# === SIDEBAR NAVIGATION ===
st.sidebar.title("📘 Navigation")
page = st.sidebar.radio("Go to", ["About FidSync", "How to Use", "Fund Scorecard"])

# === PAGE LOADER UTILITY ===
def run_page(file_path):
    spec = importlib.util.spec_from_file_location("page_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run()

# === PAGE ROUTING ===
page_map = {
    "About FidSync": "pages/About_FidSync.py",
    "How to Use": "pages/How_to_Use.py",
    "Fund Scorecard": "pages/fund_scorecard.py",
}

page_path = page_map.get(page)

if os.path.exists(page_path):
    run_page(page_path)
else:
    st.error(f"❌ Could not load page: {page_path}")
