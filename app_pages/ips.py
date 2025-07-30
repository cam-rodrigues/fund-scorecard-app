import re
import streamlit as st
import pdfplumber
import pandas as pd

# ──────────────────────────────────────────────────────────────────────────
# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {year}"
        return f"As of {month}/{day}/{year}"
    return None

# ──────────────────────────────────────────────────────────────────────────
# === Step 1: Page 1 Extraction ===
def process_page1(text):
    st.subheader("Page 1 Metadata")
    report_date = extract_report_date(text)
    st.session_state['report_date'] = report_date
    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state['total_options'] = int(m.group(1)) if m else None
    st.write(f"- Total Options: {st.session_state['total_options']}")

# ──────────────────────────────────────────────────────────────────────────
# === Step 2: TOC Extraction ===
def process_toc(text):
    st.subheader("Table of Contents Pages")
    m = re.search(r"Fund Scorecard\s+(\d{1,3})", text or "")
    st.session_state['scorecard_page'] = int(m.group(1)) if m else None
    st.write(f"- Fund Scorecard: {st.session_state['scorecard_page']}")

# ──────────────────────────────────────────────────────────────────────────
# === Step 3: Scorecard Metrics ===
def step3_process_scorecard(pdf, start_page, declared_total):
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None: lines = lines[idx+1:]
    blocks = []
    name = None
    metrics = []
    for i, line in enumerate(lines):
        m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
        if not m: continue
        metric, _, info = m.groups()
        if metric == "Manager Tenure":
            if name and metrics:
                blocks.append({"Fund Name": name, "Metrics": metrics})
            prev = next((lines[j].strip() for j in range(i-1, -1, -1) if lines[j].strip()), "")
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            metrics = []
        metrics.append({"Metric": metric, "Info": info.strip()})
    if name and metrics:
        blocks.append({"Fund Name": name, "Metrics": metrics})
    st.session_state['fund_blocks'] = blocks
    count = len(blocks)
    st.write(f"- Declared: {declared_total}, Extracted: {count}")

# ──────────────────────────────────────────────────────────────────────────
# === Step 4: IPS Screening & Table ===
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
    st.subheader("IPS Screening Results")
    rows = []
    tick_map = st.session_state.get('tickers', {})

    for b in st.session_state.get('fund_blocks', []):
        name = b['Fund Name']
        ticker = tick_map.get(name, '')
        statuses = {}
        # tenure
        info = next((m['Info'] for m in b['Metrics'] if m['Metric']=='Manager Tenure'), "")
        yrs = float(re.search(r"(\d+\.?\d*)", info).group(1)) if re.search(r"(\d+\.?\d*)", info) else 0
        statuses[1] = (yrs >= 3)
        # other criteria
        for idx, metric in enumerate(IPS[1:], start=2):
            base = metric.split()[0]
            m = next((x for x in b['Metrics'] if x['Metric'].startswith(base)), None)
            raw = m['Info'] if m else ''
            if 'Performance' in metric:
                val = float(re.search(r"([-+]?\d*\.?\d+)%", raw).group(1)) if re.search(r"([-+]?\d*\.?\d+)%", raw) else 0
                statuses[idx] = (val > 0)
            else:
                rank = int(re.search(r"(\d+)", raw).group(1)) if re.search(r"(\d+)", raw) else 999
                statuses[idx] = (rank <= 50)
        row = {'Investment Options': name, 'Ticker': ticker}
        for i in range(1, 15):
            row[str(i)] = statuses.get(i, False)
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────
# === Main ===
def run():
    st.title("IPS Screening Pipeline with Table")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return
    with pdfplumber.open(uploaded) as pdf:
        # Step 1
        txt1 = pdf.pages[0].extract_text() or ""
        process_page1(txt1)
        # Step 2
        toc_txt = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        process_toc(toc_txt)
        # Step 3
        sp = st.session_state.get('scorecard_page')
        tot = st.session_state.get('total_options')
        if sp and tot is not None:
            step3_process_scorecard(pdf, sp, tot)
        else:
            st.error("Cannot extract scorecard metrics.")
        # (Optional) populate st.session_state['tickers'] elsewhere
        # Step 4
        step4_ips_screen()

if __name__ == "__main__":
    run()
