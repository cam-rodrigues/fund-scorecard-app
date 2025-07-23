import re
import streamlit as st
import pandas as pd
import pdfplumber

def step3_full_scorecard(pdf, scorecard_start, declared_total):
    """
    Combined Steps 3, 3.5, 3.6, and 3.7:
    - Extract each fund’s 14 metrics
    - Display only the “Info” text (3.5)
    - Validate count vs. declared total (3.6)
    - Extract all numbers from each metric’s Info (3.7)
    """
    # 1) Gather all pages in the "Fund Scorecard" section
    pages = []
    for page in pdf.pages[scorecard_start - 1:]:
        text = page.extract_text() or ""
        if "Fund Scorecard" in text:
            pages.append(text)
        else:
            break
    all_text = "\n".join(pages)
    lines = all_text.splitlines()

    # 2) Skip the "Criteria Threshold" box
    crit_idx = next((i for i, line in enumerate(lines) if "Criteria Threshold" in line), None)
    if crit_idx is not None:
        lines = lines[crit_idx + 1:]

    # 3) Parse out each fund’s 14 metrics
    fund_blocks = []
    current_fund = None
    current_metrics = []
    capturing = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
            # Fund name is the previous line
            title = lines[i - 1].strip()
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", title).strip()
            if current_fund and current_metrics:
                fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})
            current_fund, current_metrics, capturing = name, [], True
        elif capturing:
            if not line.strip() or "Fund Scorecard" in line:
                continue
            if len(current_metrics) >= 14:
                capturing = False
                continue
            m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
            if m:
                met, stat, info = m.groups()
                current_metrics.append({"Metric": met, "Status": stat, "Info": info})
    # append last
    if current_fund and current_metrics:
        fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # --- Step 3.5: Display only the Info text ---
    st.subheader("Step 3.5: Metric Info Extracted")
    for block in fund_blocks:
        st.markdown(f"**{block['Fund Name']}**")
        for m in block["Metrics"]:
            st.write(f"- {m['Info']}")

    # --- Step 3.6: Validate count ---
    st.subheader("Step 3.6: Count Validation")
    extracted = len(fund_blocks)
    st.write(f"Declared total_options: **{declared_total}** | Extracted funds: **{extracted}**")
    if extracted == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Count mismatch: expected {declared_total}, found {extracted}.")

    # --- Step 3.7: Extract numbers from each Info ---
    st.subheader("Step 3.7: Numbers Extracted from Info")
    for block in fund_blocks:
        nums = []
        for m in block["Metrics"]:
            nums.extend(re.findall(r"[-+]?\d*\.\d+|\d+", m["Info"]))
        st.markdown(f"**{block['Fund Name']}**: " + (", ".join(nums) if nums else "No numbers found"))

# Example integration into your main Streamlit run():
def run():
    st.title("MPI Tool — Combined Step 3")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # assume scorecard_page and total_options were stored earlier:
        scorecard_page = st.session_state.get("scorecard_page")
        total_options   = st.session_state.get("total_options")
        if scorecard_page and total_options is not None:
            step3_full_scorecard(pdf, scorecard_page, total_options)
        else:
            st.warning("Please complete Steps 1–2 to set scorecard_page and total_options.")
