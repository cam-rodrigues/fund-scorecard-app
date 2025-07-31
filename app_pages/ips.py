# Step 0: Upload MPI PDF
import streamlit as st

# Render a file uploader that only accepts PDF files
uploaded_mpi = st.file_uploader("Upload your MPI PDF", type=["pdf"])

# If no file has been uploaded yet, stop execution here so later steps don’t run
if not uploaded_mpi:
    st.warning("Please upload an MPI PDF to continue.")
    st.stop()

# At this point, `uploaded_mpi` is a file-like object you can pass to pdfplumber or other processors
st.success(f"Uploaded: {uploaded_mpi.name}")
