import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# Inject sidebar + global style
st.markdown("""
    <style>
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
            margin-top: 2rem;
            margin-bottom: 0.3rem;
            letter-spacing: 0.5px;
        }
        .sidebar-button {
            background: none;
            border: none;
            padding: 0.25rem 0;
            font-size: 1rem;
            color: #1c2e4a;
            text-align: left;
            cursor: pointer;
            width: 100%;
        }
        .sidebar-button:hover {
            color: #304f7a;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar header
st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)

# Custom sidebar buttons using query parameters
def nav_button(label, page):
    if st.sidebar.button(label, key=label):
        st.experimental_set_query_params(page=page)

st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
nav_button("About", "About_FidSync.py")
nav_button("How to Use", "How_to_Use.py")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
nav_button("Fund Scorecard", "fund_scorecard.py")
nav_button("User Requests", "user_requests.py")

# Load selected page module from app_pages
PAGES_DIR = "app_pages"
query_params = st.query_params.to_dict()
selected_page = query_params.get("page")

if selected_page:
    page_path = os.path.join(PAGES_DIR, selected_page)
    if os.path.exists(page_path):
        try:
            spec = importlib.util.spec_from_file_location("page", page_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.run()
        except Exception as e:
            st.error(f"❌ Failed to load page: {e}")
    else:
        st.error(f"❌ Page not found: {selected_page}")
else:
    st.markdown("### Welcome to FidSync")
    st.markdown("Use the sidebar to navigate between sections.")
