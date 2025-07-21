# write_up_info.py

import streamlit as st
import pdfplumber
import re

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
            st.session_state["mpi_pdf"] = pdf

            # === Step 1: Page 1 - Detect Quarter ===
            st.subheader("Step 1: Detect Reporting Quarter")

            page1_text = pdf.pages[0].extract_text() if pdf.pages else ""
            quarter_date = None
            quarter_label = None

            # Match the known quarter-end dates
            patterns = {
                r"3/31/20(\d{2})": "Q1, 20{}",
                r"6/30/20(\d{2})": "Q2, 20{}",
                r"9/30/20(\d{2})": "Q3, 20{}",
                r"12/31/20(\d{2})": "Q4, 20{}"
            }

            for pattern, label in patterns.items():
                match = re.search(pattern, page1_text)
                if match:
                    year_suffix = match.group(1)
                    quarter_label = label.format(year_suffix)
                    quarter_date = f"{pattern[:5]}20{year_suffix}"
                    break

            if quarter_label:
                st.success(f"Detected Quarter: {quarter_label}")
                st.session_state["reporting_quarter"] = quarter_label
            else:
                st.error("Could not determine the reporting quarter from page 1.")

    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
