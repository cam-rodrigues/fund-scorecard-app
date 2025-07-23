# page_module.py or write_up_output.py or any routed Streamlit page

import streamlit as st
import pdfplumber

def run():
    st.set_page_config(page_title="Upload MPI PDF", layout="wide")
    st.title("Upload MPI PDF")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_pdf")

    if uploaded_file:
        st.success("MPI PDF uploaded successfully.")
        with pdfplumber.open(uploaded_file) as pdf:
            first_page = pdf.pages[0].extract_text()
            st.subheader("Page 1 Preview")
            st.text(first_page)
