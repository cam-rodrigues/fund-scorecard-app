import streamlit as st
import importlib.util
import os

# === Streamlit page config ===
st.set_page_config(
    page_title="FidSync",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Header with Logo ===
st.markdown(
    '''
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="https://i.imgur.com/VB0K4JG.png" alt="FidSync Logo" width="48"/>
        <h1 style="margin-bottom: 0;">FidSync</h1>
    </div>
    ''',
    unsafe_allow_html=True
)

# === Sidebar Navigation ===
st.sidebar.title("📘 Navigation")
page = st.sidebar.radio("Go to", ["About FidSync", "How to Use", "Fund Scorecard"])

# === Dynamic Page Loader ===
def run_page(file_path):
    if not os.path.exists(file_path):
        st.error(f"❌ File not found: {file_path}")
        return
    try:
        spec = importlib.util.spec_from_file_location("page_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
    except Exception as e:
        st.error(f"❌ Could not load page: {file_path}")
        st.exception(e)

# === Route to Pages in app_pages/ ===
page_map = {
    "About FidSync": "app_pages/About_FidSync.py",
    "How to Use": "app_pages/How_to_Use.py",
    "Fund Scorecard": "app_pages/fund_scorecard.py",
}

run_page(page_map[page])
