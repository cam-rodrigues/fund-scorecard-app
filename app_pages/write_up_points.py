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

# === Step 3: Extract Criteria Threshold Metrics from Fund Scorecard Section ===
import re
import streamlit as st
import pdfplumber

def run():
    st.set_page_config(page_title="Step 3: Fund Scorecard Metrics", layout="wide")
    st.title("Step 3: Extract Scorecard Metrics from 'Fund Scorecard' Section")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step3")
    if not uploaded_file:
        st.stop()

    scorecard_page_num = st.session_state.get("scorecard_page")
    if not scorecard_page_num:
        st.error("Scorecard page number not found. Please run Step 2 first.")
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        if scorecard_page_num >= len(pdf.pages):
            st.error(f"Page {scorecard_page_num} not found in PDF.")
            st.stop()

        scorecard_text = pdf.pages[scorecard_page_num - 1].extract_text()

    # Display raw page text for inspection
    with st.expander(f"Fund Scorecard Page {scorecard_page_num} Preview"):
        st.text(scorecard_text)

    # Find the Criteria Threshold section
    criteria_section = []
    if "Criteria Threshold" in scorecard_text:
        lines = scorecard_text.splitlines()
        start_index = next((i for i, line in enumerate(lines) if "Criteria Threshold" in line), None)
        if start_index is not None:
            for line in lines[start_index + 1:]:
                # Stop if we hit a blank line or next section
                if line.strip() == "" or re.match(r"^\s*Ticker\s+|^\s*Fund Name", line, re.IGNORECASE):
                    break
                criteria_section.append(line.strip())

    # Save and display
    st.session_state["scorecard_metrics"] = criteria_section

    st.subheader("Extracted Scorecard Metrics (from 'Criteria Threshold')")
    if criteria_section:
        for i, metric in enumerate(criteria_section, 1):
            st.write(f"{i}. {metric}")
    else:
        st.warning("Could not extract scorecard metrics from this page.")


# === Step 3.5: Extract Investment Option Metrics as Tables ===
import re
import streamlit as st
import pdfplumber
import pandas as pd

def run():
    st.set_page_config(page_title="Step 3.5: Extract Fund Metrics", layout="wide")
    st.title("Step 3.5: Extract Metric Tables for Each Investment Option")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step35")
    if not uploaded_file:
        st.stop()

    scorecard_page_num = st.session_state.get("scorecard_page")
    if not scorecard_page_num:
        st.error("Scorecard page number not found. Please run Step 2 first.")
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        scorecard_pages = []
        for page in pdf.pages[scorecard_page_num - 1:]:
            page_text = page.extract_text()
            if "Fund Scorecard" in (page_text or ""):
                scorecard_pages.append(page_text)
            else:
                break

    full_scorecard_text = "\n".join(scorecard_pages)
    lines = full_scorecard_text.splitlines()

    # Extract all fund blocks
    fund_blocks = []
    current_fund = None
    current_metrics = []
    capture = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
            # Line before this is likely the Investment Option title
            fund_line = lines[i - 1].strip()
            fund_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", fund_line).strip()
            if current_fund and current_metrics:
                fund_blocks.append({
                    "Fund Name": current_fund,
                    "Metrics": current_metrics
                })
            current_fund = fund_name
            current_metrics = []
            capture = True
        elif capture:
            if line.strip() == "" or "Fund Scorecard" in line or "Prepared For" in line:
                continue
            if len(current_metrics) >= 14:
                capture = False
                continue
            metric_match = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
            if metric_match:
                metric_name, status, reason = metric_match.groups()
                current_metrics.append({
                    "Metric": metric_name.strip(),
                    "Status": status.strip(),
                    "Info": reason.strip()
                })

    if current_fund and current_metrics:
        fund_blocks.append({
            "Fund Name": current_fund,
            "Metrics": current_metrics
        })

    # Save to session state
    st.session_state["fund_blocks"] = fund_blocks

    # Display all tables
    st.subheader("Extracted Metric Tables by Investment Option")
    for block in fund_blocks:
        st.markdown(f"### {block['Fund Name']}")
        df = pd.DataFrame(block["Metrics"])
        st.table(df)

# === Step 3.6: Double Check Investment Option Count ===
import streamlit as st

def run():
    st.set_page_config(page_title="Step 3.6: Verify Option Count", layout="wide")
    st.title("Step 3.6: Double Check Investment Option Count")

    fund_blocks = st.session_state.get("fund_blocks")
    total_options = st.session_state.get("total_options")

    if fund_blocks is None or total_options is None:
        st.warning("Please complete Step 1.5 and Step 3.5 before running this check.")
        st.stop()

    extracted_count = len(fund_blocks)

    st.subheader("Comparison Result")
    st.write(f"**Declared in Page 1:** {total_options}")
    st.write(f"**Extracted from Fund Scorecard:** {extracted_count}")

    if extracted_count == total_options:
        st.success("✅ Count matches: All investment options were successfully extracted.")
    else:
        st.error(f"❌ Count mismatch: Expected {total_options}, but found {extracted_count}.")
