import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# === Clean sidebar style ===
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 1px solid #ccc;
        }
        [data-testid="stSidebar"] .stButton>button {
            background-color: #ffffff;
            color: #1c2e4a;
            border: 1px solid #ccc;
            border-radius: 0.5rem;
            padding: 0.4rem 0.75rem;
            font-weight: 600;
            width: 100%;
            text-align: left;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: #e6e6e6;
            color: #000000;
        }
    </style>
""", unsafe_allow_html=True)

def load_page(page_file):
    page_path = os.path.join("app_pages", page_file)
    if os.path.exists(page_path):
        spec = importlib.util.spec_from_file_location("module.name", page_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "run"):
            module.run()
        else:
            st.error(f"⚠️ Page '{page_file}' is missing a `run()` function.")
    else:
        st.error(f"❌ Could not load page: {page_file}")

def main():
    st.sidebar.title("FidSync Navigation")

    if st.sidebar.button("Getting Started"):
        load_page("Getting_Started.py")
    elif st.sidebar.button("How to Use"):
        load_page("How_to_Use.py")
    elif st.sidebar.button("Fund Scorecard"):
        load_page("fund_scorecard.py")
    elif st.sidebar.button("User Requests"):
        load_page("user_requests.py")
    elif st.sidebar.button("Security Policy"):
        load_page("Security_Policy.py")
    else:
        st.markdown("### Welcome to FidSync")
        st.info("Use the sidebar to begin.")

if __name__ == "__main__":
    main()
