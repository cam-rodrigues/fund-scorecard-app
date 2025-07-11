import streamlit as st
import os
from PIL import Image

st.set_page_config(page_title="FidSync Beta", layout="wide")

# === Sidebar Styles ===
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #f4f6fa;
        border-right: 1px solid #d3d3d3;
        padding-top: 1.25rem;
        padding-bottom: 0;
    }

    [data-testid="stSidebar"] img {
        display: block;
        margin: 0 auto 0.2rem auto;
        width: 100%;
        max-width: 160px;
        height: auto;
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

# === Logo ===
logo_path = os.path.join("assets", "logo.png")
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.image(logo, use_container_width=True)
else:
    st.sidebar.warning("Logo not found")

st.sidebar.markdown("<hr />", unsafe_allow_html=True)

# === Navigation ===
st.sidebar.markdown('<div class="sidebar-section-title">Documentation</div>', unsafe_allow_html=True)
st.sidebar.button("Getting Started")
st.sidebar.button("Capabilities & Potential")

st.sidebar.markdown('<div class="sidebar-section-title">Tools</div>', unsafe_allow_html=True)
st.sidebar.button("Fund Scorecard")
st.sidebar.button("Fund Scorecard Metrics")
st.sidebar.button("Article Analyzer")
st.sidebar.button("Data Scanner")
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

# Legacy redirects
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
