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
            padding-left: 0.15rem;
            padding-right: none;
            position: relative;
            z-index: 1;
        }

        [data-testid="stSidebar"]::after {
            content: "";
            position: absolute;
            top: none;
            right: 0;
            width: 2px;
            height: 100%;
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
            margin-top: -1rem;
            margin-bottom: 1.5rem;
            margin-left: 0.3rem;
            padding-left: 2rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: flex-start;

        }

        .sidebar-title-container {
            position: relative;
            display: inline-block;
            transform: scale(1.35);
            transform-origin: top left;
            text align: left;
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
            left: 4.8rem;
            transform: none;
            background-color: #2b6cb0;
            color: white;
            font-size: 0.48rem;
            font-weight: 700;
            padding: 0.05rem 0.25rem;
            border-radius: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            white-space: nowrap;
            z-index: 2;

            opacity: 0;
            animation: fadeScaleUp 0.5s ease-out 0.7s forwards;
        }


        .sidebar-section {
            font-size: 0.85rem;
            font-weight: 600;
            color: #666;
            margin-top: 2rem;
            margin-bottom: 0.3rem;
            letter-spacing: 0.5px;
        }


        @keyframes fadeScaleUp {
            0% {
                opacity: 0;
                transform: translateX(-50%) scale(0.8);
            }
            100% {
                opacity: 1;
                transform: translateX(-50%) scale(1);
            }
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
    st.markdown("""
        <style>
        .welcome-container {
            padding: 1.5rem 2rem;
            background-color: #f9fbfe;
            border: 1px solid #d3e0ee;
            border-radius: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            margin-top: 1.5rem;
        }

        .welcome-title {
            font-size: 2.3rem;
            font-weight: 800;
            color: #102542;
            margin-bottom: 0.5rem;
        }

        .welcome-sub {
            font-size: 1.1rem;
            color: #3a4a5c;
            margin-bottom: 1.5rem;
        }

        .welcome-highlight {
            background-color: #dbeafe;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-weight: 600;
            color: #1e3a8a;
            display: inline-block;
            margin-top: 1rem;
        }

        .welcome-container ul {
            margin-left: 1.25rem;
        }

        .welcome-container li {
            margin-bottom: 0.6rem;
            font-size: 0.95rem;
            color: #1f2937;
        }
        </style>
        
        <div class="welcome-container">
            <div class="welcome-title">Welcome to FidSync Beta</div>
            <div class="welcome-sub">
                Your streamlined financial data toolkit for comparing, analyzing, and presenting fund performance.
            </div>

            <ul>
                <li><strong>Explore Fund Scorecards</strong> — Evaluate fund performance and watchlist status.</li>
                <li><strong>Compare Quarters</strong> — Track changes in fund criteria and positioning over time.</li>
                <li><strong>Scan Articles</strong> — Turn financial news into structured, actionable summaries.</li>
                <li><strong>Search Companies</strong> — Quickly look up firm-level data across sectors.</li>
            </ul>

            <div class="welcome-highlight">Start by selecting a tool from the sidebar.</div>
        </div>
    """, unsafe_allow_html=True)
