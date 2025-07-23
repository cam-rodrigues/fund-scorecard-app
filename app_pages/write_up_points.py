import re
import streamlit as st
import pdfplumber
import pandas as pd

# === Utility: Extract Quarter from Date String ===
def extract_quarter_label(date_text):
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

# === Step 1: Extract Quarter ===
def step1_extract_quarter(first_page_text):
    quarter_label = extract_quarter_label(first_page_text or "")
    if quarter_label:
        st.session_state["quarter_label"] = quarter_label
        st.success(f"Detected Quarter: {quarter_label}")
    else:
        st.error("Could not determine the reporting quarter from the first page.")

# === Step 1.5: Extract Page 1 Metadata ===
def step1_5_metadata(first_page_text):
    options_match = re.search(r"Total Options:\s*(\d+)", first_page_text or "")
    total_options = int(options_match.group(1)) if options_match else None
    prepared_for_match = re.search(r"Prepared For:\s*\n(.*)", first_page_text or "")
    prepared_by_match = re.search(r"Prepared By:\s*\n(.*)", first_page_text or "")
    prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else None
    prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else None

    st.session_state["total_options"] = total_options
    st.session_state["prepared_for"] = prepared_for
    st.session_state["prepared_by"] = prepared_by

    st.subheader("Extracted Info from Page 1")
    st.write(f"**Total Options:** {total_options if total_options is not None else 'Not found'}")
    st.write(f"**Prepared For:** {prepared_for or 'Not found'}")
    st.write(f"**Prepared By:** {prepared_by or 'Not found'}")

# === Step 2: Extract TOC Pages ===
def step2_extract_toc(page2_text):
    patterns = {
        "performance_page": r"Fund Performance: Current vs\. Proposed Comparison\s+(\d+)",
        "scorecard_page":   r"Fund Scorecard\s+(\d+)",
        "factsheets_page":  r"Fund Factsheets\s+(\d+)"
    }
    st.subheader("Extracted Section Start Pages")
    for key, pattern in patterns.items():
        match = re.search(pattern, page2_text)
        page_number = int(match.group(1)) if match else None
        st.session_state[key] = page_number
        st.write(f"**{key.replace('_', ' ').title()}:** {page_number or 'Not found'}")

# === Step 3: Extract Fund Scorecard + Steps 3.5–3.7 ===
def step3_scorecard_section(pdf, scorecard_start, declared_total):
    # Gather all scorecard pages
    scorecard_pages = []
    for page in pdf.pages[scorecard_start - 1:]:
        text = page.extract_text() or ""
        if "Fund Scorecard" in text:
            scorecard_pages.append(text)
        else:
            break

    full_text = "\n".join(scorecard_pages)
    lines = full_text.splitlines()

    # Skip "Criteria Threshold" section
    idx = next((i for i, line in enumerate(lines) if "Criteria Threshold" in line), None)
    if idx is not None:
        lines = lines[idx + 1:]

    # Extract each fund block of 14 metrics
    fund_blocks = []
    current_fund = None
    current_metrics = []
    capturing = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
            # The fund name is the line above
            title = lines[i - 1].strip()
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", title).strip()
            if current_fund and current_metrics:
                fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})
            current_fund = name
            current_metrics = []
            capturing = True
        elif capturing:
            if not line.strip() or "Fund Scorecard" in line:
                continue
            if len(current_metrics) >= 14:
                capturing = False
                continue
            m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
            if m:
                metric, status, info = m.groups()
                current_metrics.append({"Metric": metric, "Status": status, "Info": info})
    # Append the last fund
    if current_fund and current_metrics:
        fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Instead of tables, extract and display only the "Info" from each metric
    st.subheader("Step 3.5: Extracted Metric Info")
    for block in fund_blocks:
        st.markdown(f"### {block['Fund Name']}")
        infos = [m["Info"] for m in block["Metrics"]]
        for info in infos:
            st.write(f"- {info}")

    # Step 3.6: Validate count
    st.subheader("Step 3.6: Validate Investment Option Count")
    extracted_count = len(fund_blocks)
    st.write(f"**Declared (Page 1):** {declared_total}  |  **Extracted:** {extracted_count}")
    if extracted_count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Count mismatch: expected {declared_total}, found {extracted_count}.")

    # Step 3.7: Extract numbers from metric info
    st.subheader("Step 3.7: Numbers Found in Metric Details")
    for block in fund_blocks:
        st.markdown(f"#### {block['Fund Name']} — Numbers")
        nums = []
        for m in block["Metrics"]:
            nums.extend(re.findall(r"[-+]?\d*\.\d+|\d+", m["Info"]))
        st.write(", ".join(nums) if nums else "No numbers found.")

# === Master Run Function ===
def run():
    st.set_page_config(page_title="MPI Tool (Steps 1–3.7)", layout="wide")
    st.title("MPI Processing Tool — Steps 1 to 3.7")

    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1 & 1.5 (Page 1)
        first_text = pdf.pages[0].extract_text() or ""
        with st.expander("Page 1 Text"):
            st.text(first_text)
        step1_extract_quarter(first_text)
        step1_5_metadata(first_text)

        # Step 2 (TOC on Page 2)
        if len(pdf.pages) > 1:
            toc_text = pdf.pages[1].extract_text() or ""
            with st.expander("Page 2 (TOC)"):
                st.text(toc_text)
            step2_extract_toc(toc_text)
        else:
            st.warning("PDF has no second page for TOC.")

        # Step 3
        sc_page = st.session_state.get("scorecard_page")
        total_opts = st.session_state.get("total_options")
        if sc_page and total_opts is not None:
            step3_scorecard_section(pdf, sc_page, total_opts)
        else:
            st.warning("Missing TOC-extracted scorecard page or total options; please complete Steps 1–2.")

# Uncomment to run directly with Streamlit
# if __name__ == "__main__":
#     run()
