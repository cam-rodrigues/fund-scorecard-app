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

    st.subheader("Extracted Info")
    st.write(f"**Total Options:** {total_options if total_options is not None else 'Not found'}")
    st.write(f"**Prepared For:** {prepared_for or 'Not found'}")
    st.write(f"**Prepared By:** {prepared_by or 'Not found'}")

# === Step 2: Extract TOC Pages ===
def step2_extract_toc(page2_text):
    patterns = {
        "performance_page": r"Fund Performance: Current vs\. Proposed Comparison\s+(\d+)",
        "scorecard_page": r"Fund Scorecard\s+(\d+)",
        "factsheets_page": r"Fund Factsheets\s+(\d+)"
    }
    st.subheader("Extracted Section Start Pages")
    for key, pattern in patterns.items():
        match = re.search(pattern, page2_text)
        page_number = int(match.group(1)) if match else None
        st.session_state[key] = page_number
        st.write(f"**{key.replace('_', ' ').title()}:** {page_number or 'Not found'}")

# === Step 3: Extract Fund Scorecard Section & Validate Count & Numbers ===
def step3_scorecard_section(pdf, scorecard_start, declared_total):
    # Gather scorecard pages
    scorecard_pages = []
    for page in pdf.pages[scorecard_start - 1:]:
        text = page.extract_text()
        if "Fund Scorecard" in (text or ""):
            scorecard_pages.append(text)
        else:
            break

    full_text = "\n".join(scorecard_pages)
    lines = full_text.splitlines()

    # Skip "Criteria Threshold"
    idx = next((i for i, line in enumerate(lines) if "Criteria Threshold" in line), None)
    if idx is not None:
        lines = lines[idx + 1:]

    # Extract fund blocks
    fund_blocks = []
    current_fund = None
    current_metrics = []
    capture = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
            # Title line for fund
            title = lines[i - 1].strip()
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", title).strip()
            if current_fund and current_metrics:
                fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})
            current_fund = name
            current_metrics = []
            capture = True
        elif capture:
            if not line.strip() or "Fund Scorecard" in line:
                continue
            if len(current_metrics) >= 14:
                capture = False
                continue
            m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
            if m:
                metric, status, info = m.groups()
                current_metrics.append({"Metric": metric, "Status": status, "Info": info})
    # Append last block
    if current_fund and current_metrics:
        fund_blocks.append({"Fund Name": current_fund, "Metrics": current_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Display tables
    st.subheader("Extracted Metric Tables by Investment Option")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        df = pd.DataFrame(b["Metrics"])
        st.table(df)

    # Step 3.6: Validate Count
    st.subheader("Step 3.6: Validate Investment Option Count")
    count = len(fund_blocks)
    st.write(f"**Declared:** {declared_total}, **Extracted:** {count}")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Mismatch: expected {declared_total}, found {count}.")

    # Step 3.7: Extract Numbers
    st.subheader("Step 3.7: Numbers Found in Metric Details")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']} - Extracted Numbers")
        nums = []
        for m in b["Metrics"]:
            nums.extend(re.findall(r"[-+]?\d*\.\d+|\d+", m["Info"]))
        st.write(", ".join(nums) if nums else "No numbers found.")

# === Step 4: IPS Investment Criteria Screening ===
def step4_display_ips_and_evaluate():
    st.header("Step 4: IPS Investment Criteria Screening")

    fund_blocks = st.session_state.get("fund_blocks")
    if not fund_blocks:
        st.error("Run Step 3 first.")
        return

    IPS_METRICS = [
        "Manager Tenure",
        "3-Year Performance",
        "3-Year Performance (Peers)",
        "3-Year Sharpe Ratio",
        "3-Year Sortino Ratio",
        "5-Year Performance",
        "5-Year Performance (Peers)",
        "5-Year Sharpe Ratio",
        "5-Year Sortino Ratio",
        "Expense Ratio",
        "Investment Style"
    ]

    results = []
    for b in fund_blocks:
        name = b["Fund Name"]
        passive = "bitcoin" in name.lower()
        evals = []
        fails = 0

        for metric in IPS_METRICS:
            passed = False
            reason = ""
            if metric == "Investment Style":
                passed = True
                reason = "Always Pass"
            else:
                for m in b["Metrics"]:
                    mn, stt, info = m["Metric"], m["Status"], m["Info"]
                    low = mn.lower()
                    if metric == "3-Year Performance":
                        if (not passive and "3-year performance" in low) or (passive and "r²" in low):
                            passed = (stt == "Pass")
                            reason = info
                            break
                    elif metric == "3-Year Sortino Ratio":
                        if (not passive and "sortino" in low) or (passive and "tracking error" in low):
                            passed = (stt == "Pass")
                            reason = info
                            break
                    elif metric == "5-Year Performance":
                        if (not passive and "5-year performance" in low) or (passive and "r²" in low):
                            passed = (stt == "Pass")
                            reason = info
                            break
                    elif metric == "5-Year Sortino Ratio":
                        if (not passive and "5-year sortino" in low) or (passive and "tracking error" in low):
                            passed = (stt == "Pass")
                            reason = info
                            break
                    elif metric.lower() in low:
                        passed = (stt == "Pass")
                        reason = info
                        break
            evals.append({"IPS Metric": metric, "Status": "Pass" if passed else "Fail", "Reason": reason})
            if not passed:
                fails += 1

        if fails <= 4:
            overall = "Passed IPS Screen"
        elif fails == 5:
            overall = "Informal Watch (IW)"
        else:
            overall = "Formal Watch (FW)"

        results.append({"Fund Name": name, "Overall IPS Status": overall, "IPS Metrics": evals})

    st.session_state["ips_results"] = results

    st.subheader("IPS Screening Results")
    for r in results:
        st.markdown(f"### {r['Fund Name']}")
        st.write(f"**Status:** {r['Overall IPS Status']}")
        st.table(pd.DataFrame(r["IPS Metrics"]))

# === Master Run Function ===
def run():
    st.set_page_config(page_title="MPI Tool", layout="wide")
    st.title("MPI Processing Tool")

    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1 & 1.5
        first = pdf.pages[0].extract_text()
        with st.expander("Page 1 Text"):
            st.text(first)
        step1_extract_quarter(first)
        step1_5_metadata(first)

        # Step 2
        if len(pdf.pages) > 1:
            toc = pdf.pages[1].extract_text()
            with st.expander("Page 2 (TOC)"):
                st.text(toc)
            step2_extract_toc(toc)

        # Step 3
        sp = st.session_state.get("scorecard_page")
        to = st.session_state.get("total_options")
        if sp and to is not None:
            step3_scorecard_section(pdf, sp, to)

        # Step 4 & 4.5
        step4_display_ips_and_evaluate()

# Uncomment to run directly with Streamlit
# if __name__ == "__main__":
#     run()
