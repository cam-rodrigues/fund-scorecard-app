import streamlit as st
import os
import importlib.util

st.set_page_config(page_title="FidSync", layout="wide")

# === Sidebar Styles ===
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

# === Page Imports ===
import app_pages.about_fidsync as about
import app_pages.how_to_use as how_to_use
import app_pages.fund_scorecard as fund_scorecard
import app_pages.article_analyzer as article_analyzer

# === Page Selection ===
st.sidebar.image("assets/fidsync_logo.png", use_column_width=True)
st.sidebar.title("Navigation")

pages = {
    "About FidSync": about.run,
    "How to Use": how_to_use.run,
    "Fund Scorecard": fund_scorecard.run,
    "Article Analyzer": article_analyzer.run,
}

selection = st.sidebar.radio("Go to", list(pages.keys()))
pages[selection]()
