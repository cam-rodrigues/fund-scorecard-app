import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# === Clean, static sidebar styles ===
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 1px solid #ccc;
        }
        [data-testid="stSidebar"] .stButton>button {
            background-color: #ffffff;
            color: #1c2e4a;
            border: 1px solid #ccc;
            border-radius: 0.5rem;
            padding: 0.4rem 0.75rem;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: #e6e6e6;
            color: #000000;
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
    </style>
""", unsafe_allow_html=True)

# === Sidebar header and nav buttons ===
st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)

def nav_button(label, page):
    if st.sidebar.button(label, key=label):
        st.query_params.update({"page": page})

# === Sidebar navigation (excluding hidden admin tab) ===
st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
nav_button("Getting Started", "Getting_Started.py")
nav_button("Security Policy", "Security_Policy.py")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
nav_button("Fund Scorecard", "fund_scorecard.py")
nav_button("User Requests", "user_requests.py")

# === Page router ===
query_params = st.query_params
selected_page = query_params.get("page")
PAGES_DIR = "app_pages"

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
    # === Default landing content ===
    st.markdown("# Welcome to FidSync")
    st.markdown("""
    FidSync helps financial teams securely extract and update fund statuses from scorecard PDFs into Excel templates.

    Use the sidebar to:
    - View the **Getting Started** guide
    - Run the **Fund Scorecard** tool
    - Submit a **Request**
    """)

