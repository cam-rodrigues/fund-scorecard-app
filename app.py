import streamlit as st
import os
from PIL import Image

st.set_page_config(page_title="FidSync Beta", layout="wide")

# === Sidebar Custom Styling ===
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #f4f6fa;
        border-right: 1px solid #d3d3d3;
        padding-top: 1.25rem;
        padding-bottom: 0rem;
    }

    [data-testid="stSidebar"] img {
        display: block;
        margin: 0.5rem auto 0.25rem auto;
        width: 100%;
        max-width: 160px;
        height: auto;
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

    .sidebar-title {
        font-size: 1.7rem;
        font-weight: 800;
        color: #102542;
        padding-bottom: 0.25rem;
    }

    hr {
        border: none;
        border-top: 1px solid #c3cfe0;
        margin: 0.75rem auto;
        width: 90%;
    }
    </style>
""", unsafe_allow_html=True)

# === Logo Display (centered & proportioned) ===
logo_path = os.path.join("assets", "logo.png")
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.image(logo, use_container_width=True)
else:
    st.sidebar.warning("Logo not found in assets/logo.png")

# === Sidebar Navigation ===
st.sidebar.markdown("#### Documentation")
st.sidebar.button("Getting Started")
st.sidebar.button("Capabilities & Potential")

st.sidebar.markdown("#### Tools")
st.sidebar.button("Fund Scorecard")
st.sidebar.button("Fund Scorecard Metrics")
st.sidebar.button("Article Analyzer")
st.sidebar.button("Data Scanner")

# === Main Page Placeholder ===
st.title("Quarterly Fund Comparison Tool")
st.markdown("Upload multiple MPI PDFs (different quarters)")
st.file_uploader("Drag and drop files here", type=["pdf"], accept_multiple_files=True)
st.info("Please upload at least two MPI PDFs from different quarters.")
