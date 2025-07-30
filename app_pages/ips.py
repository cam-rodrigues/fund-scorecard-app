# ips_pipeline.py

import re
import streamlit as st
import pdfplumber

# ────────────────────────────────────────────────────────────────────────────────
# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {year}"
        return f"As of {st.session_state.get('month_name', '')} {d}, {year}"
    return None

# ────────────────────────────────────────────────────────────────────────────────
# === Step 1: Page 1 Extraction ===
def process_page1(text):
    st.subheader("Page 1 Metadata")
    # Report Date
    report_date = extract_report_date(text)
    if report_date:
        st.session_state['report_date'] = report_date
        st.success(f"Report Date: {report_date}")
    else:
        st.error("Could not detect report date on page 1.")
    # Total Options
    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state['total_options'] = int(m.group(1)) if m else None
    st.write(f"- Total Options: {st.session_state['total_options']}")

# ────────────────────────────────────────────────────────────────────────────────
# === Step 2: Table of Contents Extraction ===
def process_toc(text):
    st.subheader("Table of Contents Pages")
    patterns = {
        'scorecard_page': r"Fund Scorecard\s+(\d{1,3})",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text or "")
        st.session_state[key] = int(m.group(1)) if m else None
        st.write(f"- Fund Scorecard: {st.session_state[key]}")

# ────────────────────────────────────────────────────────────────────────────────
# === Step 3: Scorecard Metrics Extraction ===
def step3_process_scorecard(pdf, start_page, declared_total):
    st.subheader("Scorecard Metrics")
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()
    # find where metrics start
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]
    fund_blocks = []
    name = None
    metrics = []
    for i, line in enumerate(lines):
        m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
        if not m:
            continue
        metric, _, info = m.groups()
        if metric == "Manager Tenure":
            if name and metrics:
                fund_blocks.append({"Fund Name": name, "Metrics": metrics})
            prev = next((lines[j].strip() for j in range(i-1, -1, -1) if lines[j].strip()), "")
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            metrics = []
        if name:
            metrics.append({"Metric": metric, "Info": info.strip()})
    if name and metrics:
        fund_blocks.append({"Fund Name": name, "Metrics": metrics})
    st.session_state["fund_blocks"] = fund_blocks
    count = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**, Extracted: **{count}**")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Expected {declared_total}, found {count}.")

# ────────────────────────────────────────────────────────────────────────────────
# === Step 4: IPS Screening ===
def step4_ips_screen():
    IPS = [
        "Manager Tenure",
        "Excess Performance (3Yr)",
        "R‑Squared (3Yr)",
        "Peer Return Rank (3Yr)",
        "Sharpe Ratio Rank (3Yr)",
        "Sortino Ratio Rank (3Yr)",
        "Tracking Error Rank (3Yr)",
        "Excess Performance (5Yr)",
        "R‑Squared (5Yr)",
        "Peer Return Rank (5Yr)",
        "Sharpe Ratio Rank (5Yr)",
        "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (5Yr)",
        "Expense Ratio Rank"
    ]
    st.subheader("IPS Investment Criteria Screening")

    for b in st.session_state.get("fund_blocks", []):
        name = b["Fund Name"]
        statuses, reasons = {}, {}

        # Manager Tenure ≥3
        info = next((m["Info"] for m in b["Metrics"] if m["Metric"]=="Manager Tenure"), "")
        yrs = float(re.search(r"(\d+\.?\d*)", info).group(1)) if re.search(r"(\d+\.?\d*)", info) else 0
        statuses["Manager Tenure"] = (yrs >= 3)
        reasons["Manager Tenure"] = f"{yrs} yrs {'≥3' if yrs>=3 else '<3'}"

        # Other metrics
        for metric in IPS[1:]:
            base = metric.split()[0]
            m = next((x for x in b["Metrics"] if x["Metric"].startswith(base)), None)
            raw = m["Info"] if m else ""
            ok = False
            if "Excess Performance" in metric:
                val = float(re.search(r"([-+]?\d*\.\d+)%", raw).group(1)) if re.search(r"([-+]?\d*\.\d+)%", raw) else 0
                ok = (val > 0)
                reasons[metric] = f"{val}%"
            elif "R‑Squared" in metric:
                pct = float(re.search(r"(\d+\.\d+)%", raw).group(1)) if re.search(r"(\d+\.\d+)%", raw) else 0
                ok = True
                reasons[metric] = f"{pct}%"
            else:
                rank = int(re.search(r"(\d+)", raw).group(1)) if re.search(r"(\d+)", raw) else 999
                ok = (rank <= 50)
                reasons[metric] = f"Rank {rank}"
            statuses[metric] = ok

        fails = sum(not v for v in statuses.values())
        overall = "Passed IPS Screen" if fails<=4 else ("Informal Watch (IW)" if fails==5 else "Formal Watch (FW)")

        st.markdown(f"### {name}")
        st.write(f"**Overall:** {overall} ({fails} fails)")
        for crit in IPS:
            sym = "✅" if statuses.get(crit, False) else "❌"
            st.write(f"- {sym} **{crit}**: {reasons.get(crit,'—')}")

# ────────────────────────────────────────────────────────────────────────────────
# === Main pipeline ===
def run():
    st.title("IPS Screening Pipeline")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    # warm up month names for extract_report_date
    st.session_state['month_name'] = ""

    with pdfplumber.open(uploaded) as pdf:
        # Step 1
        text1 = pdf.pages[0].extract_text() or ""
        process_page1(text1)

        # Step 2 (scan first 3 pages)
        toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        process_toc(toc_text)

        # Step 3
        sc_page = st.session_state.get('scorecard_page')
        tot     = st.session_state.get('total_options')
        if sc_page and tot is not None:
            step3_process_scorecard(pdf, sc_page, tot)
        else:
            st.error("Missing scorecard page or total options, cannot extract metrics.")

        # Step 4
        step4_ips_screen()

if __name__ == "__main__":
    run()
