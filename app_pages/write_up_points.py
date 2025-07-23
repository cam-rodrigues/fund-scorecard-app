import re
import streamlit as st
import pdfplumber

# === Step 0 ===
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

# === Step 1: Extract Quarter from Page 1 ===
def extract_quarter_label(date_text):
    """Given a date string like 03/31/2025, return '1st QTR, 2025'."""
    match = re.search(r'(\d{1,2})/(\d{1,2})/(20\d{2})', date_text)
    if not match:
        return None

    month, day, year = int(match.group(1)), int(match.group(2)), match.group(3)

    if month == 3 and day == 31:
        return f"1st QTR, {year}"
    elif month == 6:
        return f"2nd QTR, {year}"
    elif month == 9 and day == 30:
        return f"3rd QTR, {year}"
    elif month == 12 and day == 31:
        return f"4th QTR, {year}"
    else:
        return f"Unknown Quarter ({match.group(0)})"

def run():
    st.set_page_config(page_title="Step 1: Extract Quarter", layout="wide")
    st.title("Step 1: Determine Quarter from Page 1")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step1")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        first_page_text = pdf.pages[0].extract_text()

    # Display raw first page text (optional)
    with st.expander("First Page Text Preview"):
        st.text(first_page_text)

    # Extract and determine quarter label
    quarter_label = extract_quarter_label(first_page_text or "")

    if quarter_label:
        st.session_state["quarter_label"] = quarter_label
        st.success(f"Detected Quarter: {quarter_label}")
    else:
        st.error("Could not determine the reporting quarter from the first page.")

