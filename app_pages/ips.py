import streamlit as st
import pdfplumber

def run_step_1():
    st.title("Write-Up Tool")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_mpi")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        # Metadata
        st.subheader("Step 1: PDF Metadata")
        st.write("**Total Pages:**", len(pdf.pages))
        st.write("**PDF Info:**", pdf.metadata)
