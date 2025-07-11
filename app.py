import streamlit as st
import os
from PIL import Image
import importlib.util

st.set_page_config(page_title="FidSync Beta", layout="wide")

# === Main Page Logo (Top-Left) ===
logo_path = os.path.join("assets", "fidsync_logo.png")
if os.path.exists(logo_path):
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image(logo_path, width=160)
    with col2:
        st.markdown("### ")  # slight spacing if needed
else:
    st.warning("Logo not found")

# === Sidebar Styles ===
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #f4f6fa;
        border-right: 1px solid #d3d3d3;
        padding-top: 1.25rem;
        padding-bottom: 0;
    }
    [data-testid="stSidebar"] hr {
        border: none;
        border-top: 1px solid #c3cfe0;
        margin: 0.5rem auto 1rem auto;
        width: 90%;
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
    .sidebar-section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #545454;
        margin-top: 0.75rem;
        margin-bottom: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# === Sidebar Navigation ===
st.sidebar.markdown('<div class="sidebar-section-title">Documentation</div>', unsafe_allow_html=True)
nav_button("Getting Started", "getting_started.py")
nav_button("Capabilities & Potential", "capabilities_and_potential.py")

st.sidebar.markdown('<div class="sidebar-section-title">Tools</div>', unsafe_allow_html=True)
nav_button("Fund Scorecard", "fund_scorecard.py")
nav_button("Fund Scorecard Metrics", "fund_scorecard_metrics.py")
nav_button("Article Analyzer", "article_analyzer.py")
nav_button("Data Scanner", "data_scanner.py")
st.sidebar.button("Company Lookup")

st.sidebar.markdown('<div class="sidebar-section">Under Construction</div>', unsafe_allow_html=True)
nav_button("Fund Summary", "fund_summary.py")
nav_button("Fund Comparison", "fund_comparison.py")
nav_button("Multi Fund Comparison", "multi_fund_comparison.py")
nav_button("Quarterly Comparison", "qtrly_comparison.py")

# === Page Router Logic ===
query_params = st.query_params
selected_page = query_params.get("page")
PAGES_DIR = "app_pages"

# Handle legacy redirects
legacy_redirects = {
    "company_scraper.py": "data_scanner.py"
}
if selected_page in legacy_redirects:
    selected_page = legacy_redirects[selected_page]
    st.query_params.update({"page": selected_page})
    st.rerun()

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
        st.warning(f"Page '{selected_page}' was not found. Redirecting to homepage.")
        st.query_params.clear()
        st.rerun()
else:
    st.markdown("# Welcome to FidSync Beta")
    st.markdown("""
    **FidSync Beta** is a data processing toolkit designed to streamline and modernize workflows by turning raw data into clear, actionable results.
    """)
