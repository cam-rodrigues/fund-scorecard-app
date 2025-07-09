import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# === Clean, static sidebar styles ===
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f4f6fa;
            border-right: 1px solid #d3d3d3;
        }
        [data-testid="stSidebar"] .stButton>button {
            background-color: #e8eef8;
            color: #1a2a44;
            border: 1px solid #c3cfe0;
            border-radius: 0.5rem;
            padding: 0.4rem 0.75rem;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: #cbd9f0;
            color: #000000;
        }
        .sidebar-title {
            font-size: 1.7rem;
            font-weight: 800;
            color: #102542;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #b4c3d3;
            margin-bottom: 1rem;
        }
        .sidebar-section {
            font-size: 0.85rem;
            font-weight: 600;
            color: #666;
            margin-top: 2rem;
            margin-bottom: 0.3rem;
            letter-spacing: 0.5px;
        }
    </style>
""", unsafe_allow_html=True)

# === Sidebar header and nav buttons ===
st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)

def nav_button(label, filename):
    if st.sidebar.button(label, key=label):
        st.query_params.update({"page": filename})

# === Sidebar navigation ===
st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
nav_button("Getting Started", "Getting_Started.py")
nav_button("Security Policy", "Security_Policy.py")
nav_button("Capabilities & Potential", "Capabilities_and_Potential.py")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
nav_button("Fund Scorecard", "fund_scorecard.py")
nav_button("Article Analyzer", "article_analyzer.py")  # <-- New Tool Added
nav_button("Conpany Scraper", "company_scraper.py")
nav_button("User Requests", "user_requests.py")

# === Page router ===
query_params = st.query_params
selected_page = query_params.get("page")
PAGES_DIR = "app_pages"

if selected_page:
    page_path = os.path.join(PAGES_DIR, selected_page)

    if os.path.exists(page_path):
        try:
            spec = importlib.util.spec_from_file_location("page_module", page_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.run()
        except Exception as e:
            st.error(f"❌ Failed to load page: {e}")
    else:
        st.error(f"❌ Page not found: {selected_page}")
else:
    # Default landing page
    st.markdown("# Welcome to FidSync")
    st.markdown("""
    FidSync helps financial teams securely extract and update fund statuses from scorecard PDFs into Excel templates.

    **Use the sidebar to:**
    -  View the **Getting Started** guide  
    -  Run the **Fund Scorecard**  
    -  Try the new **Article Analyzer**  
    -  Submit or review **User Requests**  
    -  Read the **Security Policy**
    """)
