import streamlit as st
import importlib
import os

# Set Streamlit page config
st.set_page_config(page_title="FidSync", layout="wide")

# === Define your app pages ===
PAGES = {
    "Welcome": "About_FidSync",
    "How to Use": "How_to_Use",
    "Fund Scorecard": "fund_scorecard",
}

# === Handle URL query (?page=Welcome) ===
query_params = st.query_params
if "page" in query_params:
    requested_page = query_params["page"]
    if requested_page in PAGES:
        st.session_state.page = requested_page

# === Initialize page in session_state ===
if "page" not in st.session_state:
    st.session_state.page = "Welcome"

# === Sidebar Logo/Title (clickable) ===
st.sidebar.markdown(
    f"""
    <a href='?page=Welcome' style='text-decoration: none; font-size: 28px; font-weight: bold; color: #1c2e4a;'>
        FidSync
    </a>
    """,
    unsafe_allow_html=True
)

# === Sidebar navigation buttons ===
for label, module_name in PAGES.items():
    if st.sidebar.button(label):
        st.session_state.page = label

# === Load and run selected module ===
selected_module = PAGES[st.session_state.page]

try:
    module = importlib.import_module(f"app_pages.{selected_module}")
    module.run()
except Exception as e:
    st.error(f"🚨 Could not load page: `app_pages/{selected_module}.py`\n\n**Error:** {e}")
