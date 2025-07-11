import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync Beta", layout="wide")

# === Sidebar + Logo Block Styling ===
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f4f6fa;
            border-right: 1px solid #d3d3d3;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
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

        .sidebar-title-container {
            position: relative;
            display: inline-block;
            margin-top: 1rem;
            margin-bottom: 2rem;
            margin-left: 0.3rem;  /* fine-tune for centering */
            transform: scale(1.35);  /* slightly larger */
            transform-origin: top left;
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
            left: 4.55rem;  /* adjust to sit under 'y' */
            background-color: #2b6cb0;
            color: white;
            font-size: 0.48rem;
            font-weight: 700;
            padding: 0.05rem 0.25rem;
            border-radius: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            white-space: nowrap;
        }

        .sidebar-title-container::after {
            content: "";
            display: block;
            margin-top: 1.05rem;
            border-bottom: 2px solid #b4c3d3;
            width: 100%;
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

# === Sidebar logo block (scaled and centered) ===
st.sidebar.markdown(
    '''
    <div class="sidebar-title-container">
        <div class="sidebar-title">FidSync</div>
        <div class="beta-badge">BETA</div>
    </div>
    ''',
    unsafe_allow_html=True
)

def nav_button(label, filename):
    if st.sidebar.button(label, key=label):
        st.query_params.update({"page": filename})

# === Sidebar navigation ===
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

# Optional legacy redirects
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
