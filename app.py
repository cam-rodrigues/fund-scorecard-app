import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# Inject custom sidebar + global styling
st.markdown("""
    <style>
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 1px solid #ccc;
        }
        .sidebar-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1c2e4a;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #ddd;
            margin-bottom: 1rem;
        }
        .sidebar-section {
            font-size: 0.85rem;
            font-weight: 600;
            color: #444;
            margin-top: 1.8rem;
            margin-bottom: 0.3rem;
            letter-spacing: 0.5px;
        }

        /* Global text + buttons */
        section.main > div {
            padding: 2rem;
        }
        .stButton>button {
            background-color: #1c2e4a;
            color: white;
            border-radius: 6px;
        }
        .stButton>button:hover {
            background-color: #304f7a;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar header
st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)

# Sidebar sections
st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
st.sidebar.page_link("app_pages/About_FidSync.py", label="About")
st.sidebar.page_link("app_pages/How_to_Use.py", label="How to Use")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
st.sidebar.page_link("app_pages/fund_scorecard.py", label="Fund Scorecard")
st.sidebar.page_link("app_pages/user_requests.py", label="User Requests")

# Load selected page dynamically
PAGES_DIR = "app_pages"
query_params = st.query_params.to_dict()
selected_page = query_params.get("page")

if selected_page:
    page_path = os.path.join(PAGES_DIR, selected_page)
    if os.path.exists(page_path):
        spec = importlib.util.spec_from_file_location("page", page_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
    else:
        st.error(f"🚨 Could not load page: {selected_page}")
else:
    st.markdown("### Welcome to FidSync")
    st.markdown("Please select a page from the sidebar.")

