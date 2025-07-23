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
    if month == 6:
        return f"2nd QTR, {year}"
    if month == 9 and day == 30:
        return f"3rd QTR, {year}"
    if month == 12 and day == 31:
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

    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state["total_options"] = int(m.group(1)) if m else None

    m = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state["prepared_for"] = m.group(1).strip() if m else None

    m = re.search(r"Prepared By:\s*\n(.*)", text or "")
    st.session_state["prepared_by"] = m.group(1).strip() if m else None

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
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()

    # Skip the "Criteria Threshold" block
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx + 1:]

    fund_blocks = []
    curr_name = None
    curr_metrics = []

    metric_re = re.compile(r"^(Manager Tenure|.*?)\s+(Pass|Review)\s+(.+)$")

    for i, line in enumerate(lines):
        line = line.strip()
        m = metric_re.match(line)
        if not m:
            continue
        metric, _, info = m.groups()

        # Start new fund when we hit Manager Tenure
        if metric == "Manager Tenure":
            if curr_name and curr_metrics:
                fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})
            # Find the fund name in the previous non-empty line
            prev = ""
            for j in range(i-1, -1, -1):
                if lines[j].strip():
                    prev = lines[j].strip()
                    break
            curr_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            curr_metrics = []

        # Append this metric
        if curr_name:
            curr_metrics.append({"Metric": metric, "Info": info})

    # Append the last fund
    if curr_name and curr_metrics:
        fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Display key bullets
    st.subheader("Step 3.5: Key Details per Metric")
    perf_pattern = re.compile(r"\b(outperformed|underperformed)\b.*?(\d+\.?\d+%?)", re.IGNORECASE)
    peer_phrases = [
        "within its Peer Group",
        "percentile rank",
        "as calculated against its Benchmark"
    ]

    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            info = m["Info"]
            nums = re.findall(r"[-+]?\d*\.\d+%?|\d+%?", info)
            nums_str = ", ".join(nums) if nums else "—"
            perf_notes = "; ".join(f"{grp[0].capitalize()} {grp[1]}" 
                                   for grp in perf_pattern.findall(info))
            context = "; ".join(p for p in peer_phrases if p.lower() in info.lower())
            bullet = f"- **{m['Metric']}**: {nums_str}"
            if perf_notes:
                bullet += f"; {perf_notes}"
            if context:
                bullet += f"; {context}"
            st.write(bullet)

    # Count validation
    st.subheader("Step 3.6: Investment Option Count")
    extracted = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{extracted}**")
    if extracted == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Expected {declared_total}, found {extracted}.")

# === Step 4: IPS Investment Criteria Screening ===
def step4_ips_screen():
    IPS = [
        "Manager Tenure",
        "Excess Performance (3Yr)",
        "R-Squared (3Yr)",
        "Peer Return Rank (3Yr)",
        "Sharpe Ratio Rank (3Yr)",
        "Sortino Ratio Rank (3Yr)",
        "Tracking Error Rank (3Yr)",
        "Excess Performance (5Yr)",
        "R-Squared (5Yr)",
        "Peer Return Rank (5Yr)",
        "Sharpe Ratio Rank (5Yr)",
        "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (5Yr)",
        "Expense Ratio Rank"
    ]
    st.subheader("Step 4: IPS Investment Criteria Screening")
    for b in st.session_state["fund_blocks"]:
        name = b["Fund Name"]
        is_passive = "bitcoin" in name.lower()
        statuses, reasons = {}, {}

        # Manager Tenure ≥ 3 yrs
        info = next((x["Info"] for x in b["Metrics"] if x["Metric"]=="Manager Tenure"), "")
        yrs_m = re.search(r"(\d+\.?\d*)", info)
        yrs = float(yrs_m.group(1)) if yrs_m else 0
        ok = yrs >= 3
        statuses["Manager Tenure"] = ok
        reasons["Manager Tenure"] = f"{yrs} yrs"

        # Evaluate other IPS metrics
        for metric in IPS[1:]:
            m = next((x for x in b["Metrics"] if x["Metric"].startswith(metric.split()[0])), None)
            info = m["Info"] if m else ""
            # Excess Performance
            if "Excess Performance" in metric:
                val_m = re.search(r"([-+]?\d*\.\d+)%", info)
                val = float(val_m.group(1)) if val_m else 0
                ok = val > 0
                statuses[metric] = ok
                reasons[metric] = f"{val}%"
            # R-Squared
            elif "R-Squared" in metric:
                pct_m = re.search(r"(\d+\.\d+)%", info)
                pct = float(pct_m.group(1)) if pct_m else 0
                ok = (pct >= 95) if is_passive else True
                statuses[metric] = ok
                reasons[metric] = f"{pct}%"
            # Peer Return & Sharpe
            elif "Peer Return Rank" in metric or "Sharpe Ratio Rank" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                ok = rank <= 50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"
            # Sortino / Tracking Error
            elif "Sortino Ratio Rank" in metric or "Tracking Error Rank" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                if "Sortino" in metric:
                    ok = (rank <= 50) if not is_passive else True
                else:
                    ok = (rank < 90) if is_passive else True
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"
            # Expense Ratio Rank
            elif "Expense Ratio Rank" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                ok = rank <= 50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"

        # Count fails
        fail_count = sum(not v for v in statuses.values())
        if fail_count <= 4:
            overall = "Passed IPS Screen"
        elif fail_count == 5:
            overall = "Informal Watch (IW)"
        else:
            overall = "Formal Watch (FW)"

        # Display
        st.markdown(f"### {name} ({'Passive' if is_passive else 'Active'})")
        st.write(f"**Overall:** {overall} ({fail_count} fails)")
        for metric in IPS:
            sym = "✅" if statuses.get(metric, False) else "❌"
            st.write(f"- {sym} **{metric}**: {reasons.get(metric, '—')}")

# === Main Streamlit App ===
def run():
    st.title("MPI Tool — Steps 1 to 4")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return
    with pdfplumber.open(uploaded) as pdf:
        process_page1(pdf.pages[0].extract_text() or "")
        if len(pdf.pages) > 1:
            process_toc(pdf.pages[1].extract_text() or "")
        sp = st.session_state.get("scorecard_page")
        to = st.session_state.get("total_options")
        if sp and to is not None:
            step3_process_scorecard(pdf, sp, to)
            step4_ips_screen()
        else:
            st.warning("Please complete Steps 1–3 first.")

# if __name__ == "__main__":
#     run()
