import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Write-Up Info Tool", layout="wide")
    st.title("Write-Up Info Tool")

    # === Step 0: Upload MPI PDF ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")

    if not uploaded_file:
        st.warning("Please upload an MPI PDF to begin.")
        return
#--------------------------------------------------------------------------------------------
    # === Step 1: Page 1 ===
    with pdfplumber.open(uploaded_file) as pdf:
        first_page_text = pdf.pages[0].extract_text()

    # Match date pattern (e.g. 3/31/2024)
    date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_page_text)
    if date_match:
        date_str = date_match.group(1)
        year = date_str[-4:]
        if date_str.startswith("3/31"):
            quarter = f"Q1, {year}"
        elif date_str.startswith("6/30"):
            quarter = f"Q2, {year}"
        elif date_str.startswith("9/30"):
            quarter = f"Q3, {year}"
        elif date_str.startswith("12/31"):
            quarter = f"Q4, {year}"
        else:
            quarter = "Unknown"
    else:
        date_str = "Not found"
        quarter = "Unknown"

    # Save to session state and display
    st.session_state["report_quarter"] = quarter
    st.subheader("Step 1: Quarter Detected")
    st.write(f"Detected Date: **{date_str}**")
    st.write(f"Determined Quarter: **{quarter}**")

#--------------------------------------------------------------------------------------------
    # === Step 1.5: Extract Additional Page 1 Info ===

    # Extract Total Options
    total_match = re.search(r"Total Options:\s*(\d+)", first_page_text)
    total_options = int(total_match.group(1)) if total_match else None

    # Extract "Prepared For"
    prepared_for_match = re.search(r"Prepared For:\s*\n(.*)", first_page_text)
    prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else "Not found"

    # Extract "Prepared By"
    prepared_by_match = re.search(r"Prepared By:\s*\n(.*)", first_page_text)
    prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else "Not found"

    # Save to session state
    st.session_state["total_options"] = total_options
    st.session_state["prepared_for"] = prepared_for
    st.session_state["prepared_by"] = prepared_by

    # Display
    st.subheader("Step 1.5: Page 1 Summary Info")
    st.write(f"Total Options: **{total_options}**" if total_options is not None else "Total Options not found.")
    st.write(f"Prepared For: **{prepared_for}**")
    st.write(f"Prepared By: **{prepared_by}**")

