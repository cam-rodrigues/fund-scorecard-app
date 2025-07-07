import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# === Static sidebar style ===
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
    page = st.sidebar.selectbox("Go to", [
        "Getting Started",
        "How to Use",
        "Fund Scorecard",
        "User Requests",
        "Security Policy"
    ])

    page_map = {
        "Getting Started": "Getting_Started.py",
        "How to Use": "How_to_Use.py",
        "Fund Scorecard": "fund_scorecard.py",
        "User Requests": "user_requests.py",
        "Security Policy": "Security_Policy.py"
    }

    load_page(page_map[page])

if __name__ == "__main__":
    main()
