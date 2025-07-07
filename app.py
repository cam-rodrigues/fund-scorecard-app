""
import streamlit as st
import os
import importlib.util
import shutil

# === Config paths ===
LIGHT_THEME_PATH = ".streamlit/config_light.toml"
DARK_THEME_PATH = ".streamlit/config_dark.toml"
ACTIVE_CONFIG_PATH = ".streamlit/config.toml"

st.set_page_config(page_title="FidSync", layout="wide")

# === Force light sidebar styles even in dark mode ===
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f0f2f6 !important;
            border-right: 1px solid #ccc !important;
        }
        [data-testid="stSidebar"] .stButton>button {
            background-color: #ffffff !important;
            color: #1c2e4a !important;
            border: 1px solid #ccc !important;
            border-radius: 0.5rem;
            padding: 0.4rem 0.75rem;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: #e6e6e6 !important;
            color: #000000 !important;
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
        label[for^='radio-'] {
            color: #1c2e4a !important;
            font-weight: 500;
        }
        .stRadio > div {
            color: #1c2e4a !important;
        }
    </style>
""", unsafe_allow_html=True)

# === Theme toggle logic ===
def apply_theme(theme: str):
    if theme == "Light" and os.path.exists(LIGHT_THEME_PATH):
        shutil.copyfile(LIGHT_THEME_PATH, ACTIVE_CONFIG_PATH)
    elif theme == "Dark" and os.path.exists(DARK_THEME_PATH):
        shutil.copyfile(DARK_THEME_PATH, ACTIVE_CONFIG_PATH)

def restart_required():
    st.sidebar.warning("Theme applied. Please rerun the app to see changes.")

st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-section">Select Theme</div>', unsafe_allow_html=True)

theme_choice = st.sidebar.radio(
    "", ["Light", "Dark"],
    index=0 if st.session_state.get("current_theme", "Light") == "Light" else 1,
    horizontal=True,
    label_visibility="collapsed"
)

if "current_theme" not in st.session_state:
    st.session_state.current_theme = theme_choice

if theme_choice != st.session_state.current_theme:
    apply_theme(theme_choice)
    st.session_state.current_theme = theme_choice
    restart_required()

# === Navigation buttons ===
def nav_button(label, page):
    if st.sidebar.button(label, key=label):
        st.query_params.update({"page": page})

st.sidebar.markdown('<div class="sidebar-section">Documentation</div>', unsafe_allow_html=True)
nav_button("Getting Started", "Getting_Started.py")
nav_button("Security Policy", "Security_Policy.py")

st.sidebar.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
nav_button("Fund Scorecard", "fund_scorecard.py")
nav_button("User Requests", "user_requests.py")

# === Routing ===
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
    st.markdown("# Welcome to FidSync")
    st.markdown("""
    FidSync helps financial teams securely extract and update fund statuses from scorecard PDFs into Excel templates.

    Use the sidebar to:
    - View the **Getting Started** guide
    - Run the **Fund Scorecard** tool
    - Submit a **Request**
    """)
