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

# === Step 1.5: Extract Total Options, Client Name, Prepared By ===

def run():
    st.set_page_config(page_title="Step 1.5: MPI Metadata", layout="wide")
    st.title("Step 1.5: Extract Metadata from Page 1")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step15")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        first_page_text = pdf.pages[0].extract_text()

    # Display first page text (optional)
    with st.expander("First Page Text Preview"):
        st.text(first_page_text)

    # Extract Total Options
    options_match = re.search(r"Total Options:\s*(\d+)", first_page_text or "")
    total_options = int(options_match.group(1)) if options_match else None

    # Extract "Prepared For"
    prepared_for_match = re.search(r"Prepared For:\s*\n(.*)", first_page_text or "")
    prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else None

    # Extract "Prepared By"
    prepared_by_match = re.search(r"Prepared By:\s*\n(.*)", first_page_text or "")
    prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else None

    # Save to session state
    st.session_state["total_options"] = total_options
    st.session_state["prepared_for"] = prepared_for
    st.session_state["prepared_by"] = prepared_by

    # Display results
    st.subheader("Extracted Info")
    st.write(f"**Total Options:** {total_options if total_options is not None else 'Not found'}")
    st.write(f"**Prepared For:** {prepared_for or 'Not found'}")
    st.write(f"**Prepared By:** {prepared_by or 'Not found'}")

# === Step 2: Extract TOC Page Numbers ===

def run():
    st.set_page_config(page_title="Step 2: Extract TOC", layout="wide")
    st.title("Step 2: Extract TOC Section Page Numbers")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step2")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        if len(pdf.pages) < 2:
            st.error("PDF does not contain a second page.")
            st.stop()

        page2_text = pdf.pages[1].extract_text()

    # Display raw TOC text
    with st.expander("Page 2 (TOC) Text Preview"):
        st.text(page2_text)

    # Patterns to match
    patterns = {
        "performance_page": r"Fund Performance: Current vs\. Proposed Comparison\s+(\d+)",
        "scorecard_page": r"Fund Scorecard\s+(\d+)",
        "factsheets_page": r"Fund Factsheets\s+(\d+)"
    }

    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, page2_text)
        if match:
            results[key] = int(match.group(1))
            st.session_state[key] = results[key]
        else:
            results[key] = None
            st.session_state[key] = None

    # Display results
    st.subheader("Extracted Section Start Pages")
    st.write(f"**Fund Performance Page:** {results['performance_page'] or 'Not found'}")
    st.write(f"**Fund Scorecard Page:** {results['scorecard_page'] or 'Not found'}")
    st.write(f"**Fund Factsheets Page:** {results['factsheets_page'] or 'Not found'}")
