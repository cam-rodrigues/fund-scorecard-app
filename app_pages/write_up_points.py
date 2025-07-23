import re
import streamlit as st
import pdfplumber

# === Utility: Extract Quarter from Date String ===
def extract_quarter_label(text):
    m = re.search(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    if not m:
        return None
    month, day, year = int(m.group(1)), int(m.group(2)), m.group(3)
    if month == 3 and day == 31:
        return f"1st QTR, {year}"
    elif month == 6:
        return f"2nd QTR, {year}"
    elif month == 9 and day == 30:
        return f"3rd QTR, {year}"
    elif month == 12 and day == 31:
        return f"4th QTR, {year}"
    return f"Unknown ({m.group(0)})"

# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    quarter = extract_quarter_label(text)
    if quarter:
        st.session_state["quarter_label"] = quarter
        st.success(f"Detected Quarter: {quarter}")
    else:
        st.error("Could not detect quarter on page 1.")
    opts = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state["total_options"] = int(opts.group(1)) if opts else None
    pf = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state["prepared_for"] = pf.group(1).strip() if pf else None
    pb = re.search(r"Prepared By:\s*\n(.*)", text or "")
    st.session_state["prepared_by"] = pb.group(1).strip() if pb else None

    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: {st.session_state['prepared_by']}")

# === Step 2: TOC Extraction ===
def process_toc(text):
    patterns = {
        "performance_page": r"Fund Performance: Current vs\. Proposed Comparison\s+(\d+)",
        "scorecard_page":   r"Fund Scorecard\s+(\d+)",
        "factsheets_page":  r"Fund Factsheets\s+(\d+)"
    }
    st.subheader("Table of Contents Pages")
    for key, pat in patterns.items():
        m = re.search(pat, text or "")
        num = int(m.group(1)) if m else None
        st.session_state[key] = num
        st.write(f"- {key.replace('_',' ').title()}: {num}")

# === Step 3: Scorecard Extraction & Key Bullets + Count Validation ===
def step3_process_scorecard(pdf, start_page, declared_total):
    # collect all "Fund Scorecard" pages
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()

    # skip "Criteria Threshold"
    idx = next((i for i, l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    # parse each fund block by detecting the Manager Tenure metric
    fund_blocks = []
    curr_name = None
    curr_metrics = []

    for i, line in enumerate(lines):
        m = re.match(r"^(Manager Tenure|.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
        if not m:
            continue
        metric, _, info = m.groups()
        if metric == "Manager Tenure":
            # start new fund block
            if curr_name:
                fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})
            # the fund name is in the previous non-empty line
            prev = lines[i-1].strip()
            curr_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            curr_metrics = []
        # add this metric
        curr_metrics.append({"Metric": metric, "Info": info})
    # append last block
    if curr_name:
        fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Step 3.5: Key Bullets
    st.subheader("Step 3.5: Key Details per Metric")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            st.write(f"- **{m['Metric']}**: {m['Info'].strip()}")

    # Step 3.6: Count validation
    st.subheader("Step 3.6: Investment Option Count")
    count = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{count}**")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Mismatch: expected {declared_total}, found {count}.")


# === Step 4: Classify Active vs Passive ===
def classify_funds():
    fund_blocks = st.session_state.get("fund_blocks", [])
    st.subheader("Step 4: Active vs Passive Classification")
    for block in fund_blocks:
        name = block["Fund Name"]
        fund_type = "Passive" if "bitcoin" in name.lower() else "Active"
        block["Type"] = fund_type
        st.write(f"- {name}: {fund_type}")
    st.session_state["fund_blocks"] = fund_blocks

# === Main Streamlit App ===
def run():
    st.title("MPI Tool — Steps 1 to 4")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1 & 1.5
        page1_text = pdf.pages[0].extract_text() or ""
        process_page1(page1_text)

        # Step 2
        if len(pdf.pages) > 1:
            toc_text = pdf.pages[1].extract_text() or ""
            process_toc(toc_text)
        else:
            st.warning("No TOC page found.")

        # Step 3
        sp = st.session_state.get("scorecard_page")
        to = st.session_state.get("total_options")
        if sp and to is not None:
            step3_process_scorecard(pdf, sp, to)
            # Step 4
            classify_funds()
        else:
            st.warning("Please complete Steps 1–2 first.")

# Uncomment to run with Streamlit
# if __name__ == "__main__":
#     run()
