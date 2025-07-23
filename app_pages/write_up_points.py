import re
import streamlit as st
import pdfplumber
from calendar import month_name

# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    # find all mm/dd/yyyy dates
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d, y = int(month), int(day), year
        # quarter‐end logic
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {y}"
        # otherwise first date
        return f"As of {month_name[m]} {d}, {y}"
    return None

# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    date_label = extract_report_date(text)
    if date_label:
        st.session_state["report_date"] = date_label
        st.success(f"Report Date: {date_label}")
    else:
        st.error("Report date not found.")

    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state["total_options"] = int(m.group(1)) if m else None

    m = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state["prepared_for"] = m.group(1).strip() if m else None

    m = re.search(r"Prepared By:\s*\n(.*)", text or "")
    st.session_state["prepared_by"] = m.group(1).strip() if m else None

    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: {st.session_state['prepared_by']}")

# === Step 2: TOC Extraction ===
def process_toc(text):
    # Performance: first Fund Performance line
    perf_pages = re.findall(r"Fund Performance[^\d]*(\d+)", text or "")
    perf_page = int(perf_pages[0]) if perf_pages else None
    # Scorecard
    sc = re.search(r"Fund Scorecard\s+(\d+)", text or "")
    sc_page = int(sc.group(1)) if sc else None
    # Factsheets
    fs = re.search(r"Fund Factsheets\s+(\d+)", text or "")
    fs_page = int(fs.group(1)) if fs else None

    st.subheader("Table of Contents Pages")
    st.write(f"- Performance Page: {perf_page}")
    st.write(f"- Scorecard Page: {sc_page}")
    st.write(f"- Factsheets Page: {fs_page}")

    st.session_state["performance_page"] = perf_page
    st.session_state["scorecard_page"] = sc_page
    st.session_state["factsheets_page"] = fs_page

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

    # skip Criteria Threshold
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]

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

        # new fund
        if metric == "Manager Tenure":
            if curr_name and curr_metrics:
                fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})
            # find fund name above
            prev = ""
            for j in range(i-1, -1, -1):
                if lines[j].strip():
                    prev = lines[j].strip()
                    break
            curr_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            curr_metrics = []

        # append metric
        if curr_name:
            curr_metrics.append({"Metric": metric, "Info": info})

    # last fund
    if curr_name and curr_metrics:
        fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Key bullets
    st.subheader("Step 3.5: Key Details per Metric")
    perf_pattern = re.compile(r"\b(outperformed|underperformed)\b.*?(\d+\.?\d+%?)", re.IGNORECASE)
    peer_phrases = ["within its Peer Group", "percentile rank", "as calculated against its Benchmark"]

    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            info = m["Info"]
            nums = re.findall(r"[-+]?\d*\.\d+%?|\d+%?", info)
            nums_str = ", ".join(nums) if nums else "—"
            perf_notes = "; ".join(f"{grp[0].capitalize()} {grp[1]}" for grp in perf_pattern.findall(info))
            context = "; ".join(p for p in peer_phrases if p.lower() in info.lower())
            line = f"- **{m['Metric']}**: {nums_str}"
            if perf_notes:
                line += f"; {perf_notes}"
            if context:
                line += f"; {context}"
            st.write(line)

    # Count validation
    st.subheader("Step 3.6: Investment Option Count")
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
    st.subheader("Step 4: IPS Investment Criteria Screening")
    for b in st.session_state["fund_blocks"]:
        name = b["Fund Name"]
        is_passive = "bitcoin" in name.lower()
        statuses, reasons = {}, {}

        # Manager Tenure
        info = next((x["Info"] for x in b["Metrics"] if x["Metric"]=="Manager Tenure"), "")
        yrs_m = re.search(r"(\d+\.?\d*)", info)
        yrs = float(yrs_m.group(1)) if yrs_m else 0
        ok = yrs >= 3
        statuses["Manager Tenure"] = ok
        reasons["Manager Tenure"] = f"{yrs} yrs"

        # other metrics
        for metric in IPS[1:]:
            m = next((x for x in b["Metrics"] if x["Metric"].startswith(metric.split()[0])), None)
            info = m["Info"] if m else ""
            # apply each rule…
            if "Excess Performance" in metric:
                val_m = re.search(r"([-+]?\d*\.\d+)%", info)
                val = float(val_m.group(1)) if val_m else 0
                ok = val > 0
                statuses[metric] = ok
                reasons[metric] = f"{val}%"
            elif "R-Squared" in metric:
                pct_m = re.search(r"(\d+\.\d+)%", info)
                pct = float(pct_m.group(1)) if pct_m else 0
                ok = (pct >= 95) if is_passive else True
                statuses[metric] = ok
                reasons[metric] = f"{pct}%"
            elif "Peer Return Rank" in metric or "Sharpe Ratio Rank" in metric:
                r_m = re.search(r"(\d+)", info)
                rnk = int(r_m.group(1)) if r_m else 999
                ok = rnk <= 50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rnk}"
            elif "Sortino Ratio Rank" in metric or "Tracking Error Rank" in metric:
                r_m = re.search(r"(\d+)", info)
                rnk = int(r_m.group(1)) if r_m else 999
                if "Sortino" in metric:
                    ok = (rnk <= 50) if not is_passive else True
                else:
                    ok = (rnk < 90) if is_passive else True
                statuses[metric] = ok
                reasons[metric] = f"Rank {rnk}"
            elif "Expense Ratio Rank" in metric:
                r_m = re.search(r"(\d+)", info)
                rnk = int(r_m.group(1)) if r_m else 999
                ok = rnk <= 50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rnk}"

        fails = sum(not v for v in statuses.values())
        if fails <= 4:
            overall = "Passed IPS Screen"
        elif fails == 5:
            overall = "Informal Watch (IW)"
        else:
            overall = "Formal Watch (FW)"

        st.markdown(f"### {name} ({'Passive' if is_passive else 'Active'})")
        st.write(f"**Overall:** {overall} ({fails} fails)")
        for m in IPS:
            sym = "✅" if statuses.get(m, False) else "❌"
            st.write(f"- {sym} **{m}**: {reasons.get(m, '—')}")

# === Main Streamlit App ===
def run():
    st.title("MPI Tool — Steps 1 to 4")
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
            st.warning("Please complete Steps 1–3 first.")

# if __name__ == "__main__":
#     run()
