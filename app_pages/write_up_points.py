import re
import streamlit as st
import pdfplumber

def step3_full_scorecard(pdf, scorecard_start, declared_total):
    """
    Combined Steps 3, 3.5, and 3.6:
    - Extract each fund’s 14 metrics
    - Display key numbers from each metric’s Info
    - Validate count vs. declared total
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

    # 3) Parse out each fund’s metrics
    fund_blocks = []
    current_fund = None
    current_metrics = []
    capturing = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
            # Fund name is the previous non-blank line
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
                current_metrics.append({"Metric": met, "Info": info})
    # append last
    if current_fund and current_metrics:
        fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # --- Step 3.5: Show metric key numbers ---
    st.subheader("Step 3.5: Key Numbers from Each Metric")

    for block in fund_blocks:
        st.markdown(f"### {block['Fund Name']}")
        for m in block["Metrics"]:
            # extract all numbers (years, percentages, ranks, etc.)
            nums = re.findall(r"[-+]?\d*\.\d+%?|\d+%?", m["Info"])
            nums_str = ", ".join(nums) if nums else "No numbers found"
            st.write(f"- **{m['Metric']}**: {nums_str}")

    # --- Step 3.6: Validate count ---
    st.subheader("Step 3.6: Count Validation")
    extracted = len(fund_blocks)
    st.write(f"- Declared total_options: **{declared_total}**")
    st.write(f"- Extracted funds: **{extracted}**")
    if extracted == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Count mismatch: expected {declared_total}, found {extracted}.")

# === Example integration into your main Streamlit run ===
def run():
    st.title("MPI Tool — Steps 1 to 3.6")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Assume earlier steps have populated these
        scorecard_page = st.session_state.get("scorecard_page")
        total_options = st.session_state.get("total_options")
        if scorecard_page and total_options is not None:
            step3_full_scorecard(pdf, scorecard_page, total_options)
        else:
            st.warning("Please complete Steps 1–2 to set 'scorecard_page' and 'total_options'.")
