import streamlit as st
import pdfplumber
import re
import pandas as pd
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Step 1: Upload MPI PDF", layout="wide")
    st.title("Step 1: Upload MPI.pdf")

    # Step 1: Upload PDF
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step1_upload")

    if uploaded_file:
        st.success("✅ MPI PDF successfully uploaded.")
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                st.write(f"PDF contains {len(pdf.pages)} pages.")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
#put all steps here
