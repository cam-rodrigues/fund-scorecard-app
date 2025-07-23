import streamlit as st
import pdfplumber

# === Step 0: Upload MPI PDF ===
st.set_page_config(page_title="Step 0: Upload MPI PDF", layout="wide")
st.title("Step 0: Upload MPI PDF")

uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step0")

if uploaded_file:
    st.success("MPI PDF uploaded successfully.")
    st.session_state["mpi_pdf"] = uploaded_file

    # Preview first page
    with pdfplumber.open(uploaded_file) as pdf:
        first_page = pdf.pages[0].extract_text()
        st.subheader("Preview of Page 1")
        st.text(first_page)
else:
    st.info("Please upload an MPI PDF to begin.")
