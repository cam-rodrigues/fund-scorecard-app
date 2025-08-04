import streamlit as st
import os
import importlib.util

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="FidSync Beta",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Global Styles ===
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(115deg, #f7fafc 0%, #e6eef8 80%, #d4e0f7 100%);
        }
        [data-testid="stSidebar"] {
            background: #f6f8fb;
            border-right: 1.5px solid #d7e1f3;
            padding-top: 1rem;
        }
        .sidebar-logo-wrapper {
            margin-top: -0.75rem;
            margin-bottom: 2rem;
            margin-left: 0.25rem;
            padding-left: 1.2rem;
        }
        .sidebar-title-container {
            display: inline-block;
            transform: scale(1.25);
            text-align: left;
            margin-bottom: 0.1rem;
        }
        .sidebar-title {
            font-size: 2.1rem;
            font-weight: 900;
            letter-spacing: -1px;
            color: #103a5b;
        }
        .beta-badge {
            display: inline-block;
            background: #2364b3;
            color: #fff;
            font-size: 0.58rem;
            font-weight: 700;
            padding: 0.08rem 0.35rem;
            border-radius: 0.22rem;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            margin-left: 0.7rem;
        }
        .sidebar-section {
            font-size: 0.97rem;
            font-weight: 600;
            color: #4c6a8d;
            margin-top: 1.7rem;
            margin-bottom: 0.32rem;
            letter-spacing: 0.4px;
            padding-left: 0.3rem;
        }
        .nav-btn {
            display: block;
            width: 100%;
            background: none;
            border: none;
            text-align: left;
            font-size: 1.03rem;
            font-weight: 500;
            color: #194370;
            padding: 0.4rem 1.2rem 0.4rem 0.5rem;
            margin-bottom: 0.13rem;
            border-radius: 0.6rem;
            transition: background 0.12s, color 0.12s;
            outline: none !important;
        }
        .nav-btn:hover, .nav-btn:focus {
            background: #e5eefd;
            color: #122848;
        }
        .nav-btn.active {
            background: #2364b3 !important;
            color: #fff !important;
            font-weight: 700;
        }
        .stButton>button {
            width: 100%;
            margin: 0.09rem 0 0.07rem 0;
        }
        .stAlert {
            border-radius: 1.2rem !important;
            padding: 1rem !important;
            font-size: 1.1rem;
            background: #f4f7fb !important;
        }
        /* Welcome box on homepage */
        .main-welcome-card {
            background: #fff;
            border-radius: 2rem;
            box-shadow: 0 3px 24px 0 #b7d3f63c;
            padding: 2.7rem 2.2rem 2rem 2.2rem;
            max-width: 730px;
            margin: 3.5rem auto 2.5rem auto;
            border: 1.5px solid #e0e6f0;
        }
        .main-welcome-title {
            font-size: 2.6rem;
            font-weight: 900;
            letter-spacing: -1.5px;
            background: linear-gradient(90deg, #2152b6 30%, #3175c2 70%);
            color: transparent;
            -webkit-background-clip: text;
            background-clip: text;
        }
        .main-welcome-features {
            margin: 1.2rem 0 1.4rem 0;
            padding: 0;
            list-style: none;
        }
        .main-welcome-features li {
            font-size: 1.15rem;
            margin-bottom: 0.45rem;
            padding-left: 0.7rem;
            border-left: 4px solid #2364b3;
            background: #f8fafd;
            border-radius: 0.25rem;
        }
        .main-cta-btn {
            background: #2152b6;
            color: #fff;
            font-size: 1.16rem;
            font-weight: 700;
            padding: 0.56rem 1.42rem;
            border-radius: 1.2rem;
            border: none;
            margin-top: 1.25rem;
            box-shadow: 0 2px 12px #b2c9ea2a;
            cursor: pointer;
            transition: background 0.14s;
        }
        .main-cta-btn:hover {
            background: #3175c2;
        }
        .main-disclaimer {
            margin-top: 2.4rem;
            font-size: 1.01rem;
            color: #47638b;
            background: #e9f0fc;
            border-radius: 1rem;
            padding: 1.1rem 1.4rem;
        }
    </style>
""", unsafe_allow_html=True)

# === Sidebar Logo Block ===
st.sidebar.markdown('''
    <div class="sidebar-logo-wrapper">
        <div class="sidebar-title-container">
            <span class="sidebar-title">FidSync</span>
            <span class="beta-badge">BETA</span>
        </div>
    </div>
''', unsafe_allow_html=True)

# === Navigation Helper (now with active button) ===
def nav_button(label, filename, active):
    btn_style = "nav-btn active" if active else "nav-btn"
    st.sidebar.markdown(
        f'''
        <button class="{btn_style}" onclick="window.location.search='?page={filename}'">{label}</button>
        ''',
        unsafe_allow_html=True,
    )

# === Sidebar Navigation Structure ===
query_params = st.query_params
selected_page = query_params.get("page")
PAGES_DIR = "app_pages"

nav_sections = [
    {
        "title": "Documentation",
        "links": [
            ("Getting Started", "Getting_Started.py"),
            ("Capabilities & Potential", "capabilities_and_potential.py"),
            ("Resources", "resources.py"),
            ("User Requests", "user_requests.py"),
        ],
    },
    {
        "title": "Tools",
        "links": [
            ("Article Analyzer", "article_analyzer.py"),
            ("Company Lookup", "company_lookup.py"),
        ],
    },
    {
        "title": "MPI Tools",
        "links": [
            ("Fund Scorecard", "fund_scorecard.py"),
            ("Scorecard Metrics", "fund_scorecard_metrics.py"),
            ("IPS Screening", "ips_screening.py"),
            ("Writeup Generator", "write_up.py"),
            ("Writeup & Rec", "writeup_&_rec.py"),
        ],
        "expander": True,
    },
    {
        "title": "Under Construction",
        "links": [
            ("Fund Scorecard Test", "fund_scorecard_test.py"),
            ("Writeup & Rec Test", "writeup_&_rec_test.py"),
        ],
    },
]

for section in nav_sections:
    st.sidebar.markdown(
        f'<div class="sidebar-section">{section["title"]}</div>',
        unsafe_allow_html=True
    )
    if section.get("expander"):
        with st.sidebar.expander(section["title"], expanded=False):
            for label, filename in section["links"]:
                nav_button(label, filename, selected_page == filename)
    else:
        for label, filename in section["links"]:
            nav_button(label, filename, selected_page == filename)

# === Redirects for Old Page Names ===
legacy_redirects = {
    "company_scraper.py": "data_scanner.py"
}
if selected_page in legacy_redirects:
    selected_page = legacy_redirects[selected_page]
    st.query_params.update({"page": selected_page})
    st.rerun()

# === Page Router ===
if selected_page:
    page_path = os.path.join(PAGES_DIR, selected_page)
    if os.path.exists(page_path):
        try:
            spec = importlib.util.spec_from_file_location("page_module", page_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.run()
        except Exception as e:
            st.error(f"Couldn't load the selected page. Please try again or contact support.\n\nDetails: {e}")
    else:
        st.warning("Page not found. Redirecting to home...", icon=None)
        st.query_params.clear()
        st.rerun()
else:
    st.markdown(
        '''
        <div class="main-welcome-card">
            <div class="main-welcome-title">Welcome to FidSync Beta</div>
            <ul class="main-welcome-features">
                <li><b>Explore Fund Scorecards</b> — Evaluate fund performance and watchlist status</li>
                <li><b>Compare Quarters</b> — Track changes in fund criteria over time</li>
                <li><b>Scan Articles</b> — Turn financial news into structured summaries</li>
                <li><b>Search Companies</b> — Quickly look up firm-level data across sectors</li>
                <li><b>User Request</b> — Suggest changes, report bugs, or request new tools</li>
            </ul>
            <a href="?page=Getting_Started.py">
                <button class="main-cta-btn">Get Started</button>
            </a>
        </div>
        <div class="main-disclaimer">
            This content was generated using automation and may not be perfectly accurate. Please verify against official sources.
        </div>
        ''', unsafe_allow_html=True
    )

# === Required for Multipage Setup ===
def run():
    pass  # Not used, main routing is in this file

