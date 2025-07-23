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

# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    quarter = extract_quarter_label(text)
    if quarter:
        st.session_state["quarter_label"] = quarter
        st.success(f"Quarter detected: {quarter}")
    else:
        st.error("Quarter not found on page 1.")

    opts = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state["total_options"] = int(opts.group(1)) if opts else None

    pf = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state["prepared_for"] = pf.group(1).strip() if pf else None

    pb = re.search(r"Prepared By:\s*\n(.*)", text or "")
    st.session_state["prepared_by"] = pb.group(1).strip() if pb else None

    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: {st.session_state['prepared_by']}")

# === Step 2: TOC Extraction ===
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

# === Step 3: Extract & Display Key Numbers + Count Validation ===
def step3_process_scorecard(pdf, start_page, declared_total):
    # Collect "Fund Scorecard" pages
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()

    # Skip "Criteria Threshold"
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    # Parse each fund block
    fund_blocks = []
    curr_name = None
    curr_metrics = []
    capture = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
            title = lines[i-1].strip()
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", title).strip()
            if curr_name and curr_metrics:
                fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})
            curr_name, curr_metrics, capture = name, [], True
        elif capture:
            if not line.strip() or "Fund Scorecard" in line:
                continue
            if len(curr_metrics) >= 14:
                capture = False
                continue
            m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
            if m:
                metric, _, info = m.groups()
                curr_metrics.append({"Metric": metric, "Info": info})
    if curr_name and curr_metrics:
        fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Step 3.5: Show key numbers and performance notes
    st.subheader("Step 3.5: Key Numbers & Notes")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            info = m["Info"]
            # extract numbers (years, %, ranks)
            nums = re.findall(r"[-+]?\d*\.\d+%?|\d+%?", info)
            nums_str = ", ".join(nums) if nums else "—"
            # performance keywords
            perf_match = re.search(
                r"\b(outperform|underperform)\b.*?(\d+\.?\d+%?)",
                info, flags=re.IGNORECASE
            )
            perf_note = perf_match.group(0) if perf_match else ""
            # manager tenure phrases
            tenure_notes = []
            for phrase in ["within its Peer Group", "Percentile rank", "Rank", "as calculated against its benchmark"]:
                if phrase.lower() in info.lower():
                    tenure_notes.append(phrase)
            tenure_str = "; ".join(tenure_notes)

            line = f"- **{m['Metric']}**: {nums_str}"
            if perf_note:
                line += f"; {perf_note}"
            if m["Metric"] == "Manager Tenure" and tenure_str:
                line += f"; {tenure_str}"
            st.write(line)

    # Step 3.6: Count validation
    st.subheader("Step 3.6: Investment Option Count")
    count = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{count}**")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Mismatch: expected {declared_total}, found {count}.")

# === Main Streamlit App ===
def run():
    st.title("MPI Tool — Steps 1 to 3.6")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1 & 1.5
        p1 = pdf.pages[0].extract_text() or ""
        with st.expander("Page 1 Text"):
            st.text(p1)
        process_page1(p1)

        # Step 2
        if len(pdf.pages) > 1:
            toc = pdf.pages[1].extract_text() or ""
            with st.expander("Page 2 (TOC)"):
                st.text(toc)
            process_toc(toc)
        else:
            st.warning("No TOC page found.")

        # Step 3
        sp = st.session_state.get("scorecard_page")
        to = st.session_state.get("total_options")
        if sp and to is not None:
            step3_process_scorecard(pdf, sp, to)
        else:
            st.warning("Please complete Steps 1–2 first.")

# To run with Streamlit:
# if __name__ == "__main__":
#     run()
