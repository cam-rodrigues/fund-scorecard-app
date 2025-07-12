import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync Beta", layout="wide")

# === Sidebar + Logo Block Styling ===
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f4f6fa;
            border-right: none;
            padding-left: 0.5rem;
            padding-right: 0;
            position: relative;
            z-index: 1;
        }

        /* Vertical line starts BELOW the logo using pseudo-element */
        [data-testid="stSidebar"]::after {
            content: "";
            position: absolute;
            top: 7.0rem;
            right: 0;
            width: 2px;
            height: calc(100% - 7.0rem);
            background-color: #b4c3d3;
            z-index: 1;
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

        .sidebar-logo-wrapper {
            margin-top: 0.5rem;
            margin-bottom: 1.5rem;
        }

        .sidebar-title-container {
            position: relative;
            display: inline-block;
            transform: scale(1.35);
            transform-origin: top left;
            margin-left: 0.3rem;
        }

        .sidebar-title {
            font-size: 1.7rem;
            font-weight: 800;
            color: #102542;
            line-height: 1;
            white-space: nowrap;
        }

        .beta-badge {
            position: absolute;
            top: 1.62rem;
            left: 4.0rem;
            background-color: #2b6cb0;
            color: white;
            font-size: 0.48rem;
            font-weight: 700;
            padding: 0.05rem 0.25rem;
            border-radius: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            white-space: nowrap;
            z-index: 10;
        }

        .logo-underline-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin-top: 1rem;
            margin-left: 0.3rem;
            margin-right: 0;
            width: calc(100% - 0.3rem);
            height: 2px;
        }

        .line-left {
            height: 2px;
            background-color: #b4c3d3;
            width: 4.8rem;
            flex-shrink: 0;
        }

        .line-gap {
            width: 2.4rem;
            flex-shrink: 0;
        }

        .line-right {
            height: 2px;
            background-color: #b4c3d3;
            flex-grow: 1;
            min-width: 5;
            margin-left: 0.9rem;
            margin-right: 0;
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

# === Sidebar logo block ===
st.sidebar.markdown(
    '''
    <div class="sidebar-logo-wrapper">
        <div class="sidebar-title-container">
            <div class="sidebar-title">FidSync</div>
            <div class="beta-badge">BETA</div>
        </div>
        <div class="logo-underline-wrapper">
            <div class="line-left"></div>
            <div class="line-gap"></div>
            <div class="line-right"></div>
        </div>
    </div>
    ''',
    unsafe_allow_html=True
)

# === Navigation helper ===
def nav_button(label, filename):
    if st.sidebar.button(label, key=label):
        st.query_params.update({"page": filename})

# === Navigation structure ===
st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
nav_button("Getting Started", "Getting_Started.py")
nav_button("Capabilities & Potential", "capabilities_and_potential.py")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
nav_button("Fund Scorecard", "fund_scorecard.py")
nav_button("Fund Scorecard Metrics", "fund_scorecard_metrics.py")
nav_button("Article Analyzer", "article_analyzer.py")
nav_button("Data Scanner", "data_scanner.py")
nav_button("Company Lookup", "company_lookup.py")

st.sidebar.markdown('<div class="sidebar-section">Under Construction</div>', unsafe_allow_html=True)
nav_button("Fund Summary", "fund_summary.py")
nav_button("Fund Comparison", "fund_comparison.py")
nav_button("Multi Fund Comparison", "multi_fund_comparison.py")
nav_button("Quarterly Comparison", "qtrly_comparison.py")

# === Page router ===
query_params = st.query_params
selected_page = query_params.get("page")
PAGES_DIR = "app_pages"

# Redirect old names if needed
legacy_redirects = {
    "company_scraper.py": "data_scanner.py"
}
if selected_page in legacy_redirects:
    selected_page = legacy_redirects[selected_page]
    st.query_params.update({"page": selected_page})
    st.rerun()

# Load selected page
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
