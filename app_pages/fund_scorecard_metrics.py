import streamlit as st
import pdfplumber
import pandas as pd
import re

CONFIDENCE_THRESHOLD = 0.75  # below this is considered "low confidence"
DEBUG = True  # change to False if you don’t want logs at the bottom

def normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())

def simple_similarity(a, b):
    a, b = normalize_name(a), normalize_name(b)
    matches = sum((char in b) for char in a)
    return matches / max(len(a), len(b))

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Processing PDF..."):
            fund_meta = {}
            inception_data = {}
            criteria_data = []
            low_confidence_logs = []

            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)

                # === Phase 1: Fund meta (name/ticker) ===
                for i in range(min(15, total_pages)):
                    lines = pdf.pages[i].extract_text().split("\n")
                    for line in lines:
                        ticker_match = re.match(r"^(
