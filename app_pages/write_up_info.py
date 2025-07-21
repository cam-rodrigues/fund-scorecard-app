## write_up_info.py

import streamlit as st
import pdfplumber

def run():
    st.set_page_config(page_title="Write-Up Info Tool", layout="wide")
    st.title("Write-Up Info Tool")

    # === Step 0: Upload MPI PDF ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    
    if not uploaded_file:
        st.warning("Please upload an MPI PDF to proceed.")
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            st.success(f"MPI PDF successfully loaded with {len(pdf.pages)} pages.")
            # Save PDF in session state for future steps
            st.session_state["mpi_pdf"] = pdf
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
