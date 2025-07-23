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
    st.write(f"**Total Options:** {total_options if total_options else 'Not found'}")
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

# === Step 3: Extract Fund Scorecard Section & Validate Count ===
def step3_scorecard_section(pdf, scorecard_start, declared_total):
    scorecard_pages = []
    for page in pdf.pages[scorecard_start - 1:]:
        text = page.extract_text()
        if "Fund Scorecard" in (text or ""):
            scorecard_pages.append(text)
        else:
            break

    full_scorecard_text = "\n".join(scorecard_pages)
    lines = full_scorecard_text.splitlines()

    # Skip "Criteria Threshold"
    criteria_index = next((i for i, line in enumerate(lines) if "Criteria Threshold" in line), None)
    if criteria_index is not None:
        lines = lines[criteria_index + 1:]

    # Extract fund blocks
    fund_blocks = []
    current_fund = None
    current_metrics = []
    capture = False

    for i, line in enumerate(lines):
        if "Manager Tenure" in line:
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
            if line.strip() == "" or "Fund Scorecard" in line:
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

    st.session_state["fund_blocks"] = fund_blocks

    st.subheader("Extracted Metric Tables by Investment Option")
    for block in fund_blocks:
        st.markdown(f"### {block['Fund Name']}")
        df = pd.DataFrame(block["Metrics"])
        st.table(df)

    # Step 3.6: Validate Count
    st.subheader("Step 3.6: Validate Investment Option Count")
    extracted_count = len(fund_blocks)
    st.write(f"**Declared in Page 1:** {declared_total}")
    st.write(f"**Extracted from Scorecard:** {extracted_count}")
    if declared_total == extracted_count:
        st.success("✅ Count matches: All investment options were successfully extracted.")
    else:
        st.error(f"❌ Count mismatch: Expected {declared_total}, but found {extracted_count}.")

# === Master Run Function ===
def run():
    st.set_page_config(page_title="MPI Tool", layout="wide")
    st.title("Upload and Process MPI PDF")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_main")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        # === Step 1 & 1.5 ===
        first_page_text = pdf.pages[0].extract_text()
        with st.expander("Page 1 Text"):
            st.text(first_page_text)
        step1_extract_quarter(first_page_text)
        step1_5_metadata(first_page_text)

        # === Step 2 ===
        if len(pdf.pages) >= 2:
            page2_text = pdf.pages[1].extract_text()
            with st.expander("Page 2 (TOC) Text"):
                st.text(page2_text)
            step2_extract_toc(page2_text)
        else:
            st.warning("PDF does not contain a second page for TOC.")

        # === Step 3, 3.5, 3.6 ===
        scorecard_page = st.session_state.get("scorecard_page")
        declared_total = st.session_state.get("total_options")
        if scorecard_page and declared_total:
            step3_scorecard_section(pdf, scorecard_page, declared_total)
        else:
            st.warning("Missing scorecard page number or total options. Run previous steps first.")


# === Step 4: IPS Investment Criteria Screening ===
import streamlit as st
import pandas as pd

def run():
    st.set_page_config(page_title="Step 4: IPS Investment Criteria", layout="wide")
    st.title("Step 4: IPS Investment Criteria Screening")

    fund_blocks = st.session_state.get("fund_blocks")
    if not fund_blocks:
        st.error("Fund Scorecard data not found. Please run Step 3 first.")
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

    for block in fund_blocks:
        fund_name = block["Fund Name"]
        is_passive = "bitcoin" in fund_name.lower()
        metrics = block["Metrics"]

        # Initialize status for each IPS metric
        ips_result = []
        fail_count = 0

        for idx, ips_metric in enumerate(IPS_METRICS):
            passed = False
            reason = ""

            if ips_metric == "Investment Style":
                passed = True
                reason = "Always passes"
            else:
                for m in metrics:
                    mname = m["Metric"].lower()
                    minfo = m["Info"]
                    if ips_metric == "3-Year Performance":
                        if (not is_passive and "3-Year Performance" in m["Metric"]) or (is_passive and "3-Year R²" in m["Metric"]):
                            passed = "Pass" in m["Status"]
                            reason = minfo
                            break
                    elif ips_metric == "3-Year Sortino Ratio":
                        if (not is_passive and "Sortino" in mname) or (is_passive and "Tracking Error" in mname):
                            passed = "Pass" in m["Status"]
                            reason = minfo
                            break
                    elif ips_metric == "5-Year Performance":
                        if (not is_passive and "5-Year Performance" in m["Metric"]) or (is_passive and "5-Year R²" in m["Metric"]):
                            passed = "Pass" in m["Status"]
                            reason = minfo
                            break
                    elif ips_metric == "5-Year Sortino Ratio":
                        if (not is_passive and "5-Year Sortino" in mname) or (is_passive and "5-Year Tracking" in mname):
                            passed = "Pass" in m["Status"]
                            reason = minfo
                            break
                    elif ips_metric.lower() in mname:
                        passed = "Pass" in m["Status"]
                        reason = minfo
                        break

            ips_result.append({
                "IPS Metric": ips_metric,
                "Status": "Pass" if passed else "Fail",
                "Reason": reason
            })

            if not passed:
                fail_count += 1

        # Determine overall status
        if fail_count <= 4:
            status = "Passed IPS Screen"
        elif fail_count == 5:
            status = "Informal Watch (IW)"
        else:
            status = "Formal Watch (FW)"

        results.append({
            "Fund Name": fund_name,
            "IPS Metrics": ips_result,
            "Overall IPS Status": status
        })

    st.session_state["step4_results"] = results

    # === Display Results ===
    st.subheader("IPS Screening Results")
    for fund in results:
        st.markdown(f"### {fund['Fund Name']}")
        st.write(f"**Status:** {fund['Overall IPS Status']}")
        df = pd.DataFrame(fund["IPS Metrics"])
        st.table(df)
