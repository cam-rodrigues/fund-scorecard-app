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

# === Apply theme ===
def apply_theme(theme: str):
    if theme == "Light" and os.path.exists(LIGHT_THEME_PATH):
        shutil.copyfile(LIGHT_THEME_PATH, ACTIVE_CONFIG_PATH)
    elif theme == "Dark" and os.path.exists(DARK_THEME_PATH):
        shutil.copyfile(DARK_THEME_PATH, ACTIVE_CONFIG_PATH)

def restart_required():
    st.sidebar.warning("Theme applied. Please rerun the app to see changes.")

# === Sidebar theme label ===
st.sidebar.markdown(f"""
    <div style='padding: 0.5rem 0 1.5rem 0;'>
        <div style='font-size: 0.9rem; font-weight: 600; margin-bottom: 0.3rem; color: #333;'>
            Select Theme
        </div>
    </div>
""", unsafe_allow_html=True)

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

# === Inject static sidebar styles (unchanging) ===
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
        border-right: 1px solid #ccc;
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
    .sidebar-button {
        background: none;
        border: none;
        padding: 0.25rem 0;
        font-size: 1rem;
        color: #1c2e4a;
        text-align: left;
        cursor: pointer;
        width: 100%;
    }
    .sidebar-button:hover {
        color: #304f7a;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)

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
            st.error(f"\u274c Failed to load page: {e}")
    else:
        st.error(f"\u274c Page not found: {selected_page}")
else:
    st.markdown("# Welcome to FidSync")
    st.markdown("""
    FidSync helps financial teams securely extract and update fund statuses from scorecard PDFs into Excel templates.

    Use the sidebar to:
    - View the **Getting Started** guide
    - Run the **Fund Scorecard** tool
    - Submit a **Request**
    """)
