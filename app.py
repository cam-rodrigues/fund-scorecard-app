import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync Beta", layout="wide")

# ======== Sidebar + Logo Block Styling (Unchanged) =========
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
            padding: 0.45rem 0.85rem;
            font-weight: 600;
            transition: background 0.13s, color 0.13s;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: #cbd9f0;
            color: #000;
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
            text-align: left;
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
            font-size: 0.95rem;
            font-weight: 700;
            color: #314158;
            margin-top: 2.2rem;
            margin-bottom: 0.5rem;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            opacity: 0.75;
        }
        @keyframes fadeScaleUp {
            0% { opacity: 0; transform: translateX(-50%) scale(0.8);}
            100% { opacity: 1; transform: translateX(-50%) scale(1);}
        }
    </style>
""", unsafe_allow_html=True)

# ======== Sidebar Logo Block (Unchanged) =========
st.sidebar.markdown('''
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
''', unsafe_allow_html=True)

# ======= NAVIGATION =========
def nav_button(label, filename):
    # Simple navigation helper
    if st.sidebar.button(label, key=label):
        st.query_params.update({"page": filename})

# --- Sidebar sections
st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
nav_button("Getting Started", "Getting_Started.py")
nav_button("Capabilities & Potential", "capabilities_and_potential.py")
nav_button("Resources", "resources.py")
nav_button("User Requests", "user_requests.py")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
nav_button("Article Analyzer", "article_analyzer.py")
nav_button("Company Lookup", "company_lookup.py")

st.sidebar.markdown('<div class="sidebar-section">MPI Tools</div>', unsafe_allow_html=True)
with st.sidebar.expander("MPI Tools", expanded=False):
    nav_button("Fund Scorecard", "fund_scorecard.py")
    nav_button("Scorecard Metrics", "fund_scorecard_metrics.py")
    nav_button("IPS Screening", "ips_screening.py")
    nav_button("Writeup Generator", "write_up.py")
    nav_button("Writeup & Rec", "writeup_&_rec.py")

with st.sidebar.expander("Under Construction", expanded=False):
    nav_button("Fund Scorecard Test", "fund_scorecard_test.py")
    nav_button("Writeup & Rec Test", "writeup_&_rec_test.py")

# ========== PAGE ROUTER ==============
query_params = st.query_params
selected_page = query_params.get("page")
PAGES_DIR = "app_pages"

legacy_redirects = {
    "company_scraper.py": "data_scanner.py"
}
if selected_page in legacy_redirects:
    selected_page = legacy_redirects[selected_page]
    st.query_params.update({"page": selected_page})
    st.rerun()

# --- Load page, else show homepage
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
    # --- HOMEPAGE ---
    st.markdown("""
        <div style="
            margin: 2.8rem auto 0 auto; 
            padding: 2.4rem 2.8rem 2rem 2.8rem;
            max-width: 660px; 
            background: #f6f8fc; 
            border-radius: 2.5rem;
            box-shadow: 0 4px 32px rgba(40,60,90,0.07);
            ">
        <h1 style="font-size:2.2rem; font-weight:900; color:#11213b; margin-bottom:1.1rem; letter-spacing:-1.5px;">Welcome to FidSync Beta</h1>
        <p style="font-size:1.12rem; color:#39475a; margin-bottom:1.7rem;">
            Your streamlined financial data toolkit for <b>comparing</b>, <b>analyzing</b>, and <b>presenting fund performance</b>.
        </p>
        <hr style="border: none; border-top: 1.5px solid #bcd1e7; margin: 1.5rem 0;">
        <div style="font-size:1.05rem; color:#29406a;">
            <ul style="padding-left:1.1em; margin-top:0.5em;">
                <li><b>Explore Fund Scorecards</b> — Evaluate fund performance and watchlist status</li>
                <li><b>Compare Quarters</b> — Track changes in fund criteria over time</li>
                <li><b>Scan Articles</b> — Turn financial news into structured summaries</li>
                <li><b>Search Companies</b> — Quickly look up firm-level data across sectors</li>
                <li><b>User Requests</b> — Suggest changes, report bugs, or request new tools</li>
            </ul>
        </div>
        <div style="margin-top:2.3rem; margin-bottom:0.7rem;">
            <a href="?page=Getting_Started.py" style="
                display:inline-block; 
                padding: 0.7rem 2.2rem; 
                background:#2b6cb0; 
                color:white; 
                border-radius:1.8rem; 
                font-weight:700;
                font-size:1.06rem;
                letter-spacing:0.01em;
                box-shadow:0 1px 8px rgba(36,70,160,0.08);
                text-decoration:none;
                transition:background 0.13s;
            " onmouseover="this.style.background='#17406e'" onmouseout="this.style.background='#2b6cb0'">
                Get Started
            </a>
        </div>
        <p style="font-size:0.99rem; color:#687790; margin-top:1.2rem;">This content was generated using automation and may not be perfectly accurate. Please verify against official sources.</p>
        </div>
    """, unsafe_allow_html=True)

# === For multipage pattern
def run():
    main()
