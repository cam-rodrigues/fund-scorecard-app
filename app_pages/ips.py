import re
import streamlit as st
import pdfplumber
from calendar import month_name
import pandas as pd
from rapidfuzz import fuzz
from pptx import Presentation
from pptx.util import Inches
from io import BytesIO

#────────────────────────────────────────────────────────────────────────
# Utility: Extract & Label Report Date
#────────────────────────────────────────────────────────────────────────
def extract_report_date(text):
    dates = re.findall(r"(\d{1,2})/(\d{1,2})/(20\d{2})", text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = {(3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th"}[(m,d)]
            return f"{q} QTR, {year}"
        return f"As of {month_name[m]} {d}, {year}"
    return None

#────────────────────────────────────────────────────────────────────────
# Step 1 & 1.5: Page 1 Extraction
#────────────────────────────────────────────────────────────────────────
def process_page1(text):
    report_date = extract_report_date(text)
    if report_date:
        st.session_state['report_date'] = report_date
        st.success(f"Report Date: {report_date}")
    else:
        st.error("Could not detect report date on page 1.")

    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state['total_options'] = int(m.group(1)) if m else None

    m = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state['prepared_for'] = m.group(1).strip() if m else None

    m = re.search(r"Prepared By:\s*(.*)", text or "")
    pb = m.group(1).strip() if m else ""
    if not pb or "mpi stylus" in pb.lower():
        pb = "Procyon Partners, LLC"
    st.session_state['prepared_by'] = pb

    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: {pb}")

#────────────────────────────────────────────────────────────────────────
# Step 2: Table of Contents Extraction
#────────────────────────────────────────────────────────────────────────
def process_toc(text):
    perf = re.search(r"Fund Performance[^\d]*(\d{1,3})", text or "")
    sc   = re.search(r"Fund Scorecard\s+(\d{1,3})", text or "")
    fs   = re.search(r"Fund Factsheets\s+(\d{1,3})", text or "")
    st.session_state['performance_page'] = int(perf.group(1)) if perf else None
    st.session_state['scorecard_page']   = int(sc.group(1))   if sc   else None
    st.session_state['factsheets_page']  = int(fs.group(1))   if fs   else None

    st.subheader("Table of Contents Pages")
    st.write(f"- Fund Performance: {st.session_state['performance_page']}")
    st.write(f"- Fund Scorecard: {st.session_state['scorecard_page']}")
    st.write(f"- Fund Factsheets: {st.session_state['factsheets_page']}")

#────────────────────────────────────────────────────────────────────────
# Step 3: Scorecard Extraction (Pass/Fail only)
#────────────────────────────────────────────────────────────────────────
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
    if idx is not None:
        lines = lines[idx+1:]

    fund_blocks = []
    name = None
    metrics = []

    for i, line in enumerate(lines):
        match = re.match(r"^(.*?)\s+(Pass|Review)\s+", line.strip())
        if not match:
            continue
        metric, status = match.groups()

        if metric == "Manager Tenure":
            if name and metrics:
                fund_blocks.append({"Fund Name": name, "Metrics": metrics})
            prev = ""
            for j in range(i-1, -1, -1):
                if lines[j].strip():
                    prev = lines[j].strip()
                    break
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            metrics = []

        if name:
            metrics.append({"Metric": metric, "Status": status})

    if name and metrics:
        fund_blocks.append({"Fund Name": name, "Metrics": metrics})

    st.session_state["fund_blocks"] = fund_blocks
    st.subheader("Step 3.5: Scorecard Pass/Fail Details")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b['Metrics']:
            sym = "✅" if m.get('Status')=='Pass' else "❌"
            st.write(f"- {sym} {m['Metric']}")

    st.subheader("Step 3.6: Investment Option Count")
    count = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{count}**")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Expected {declared_total}, found {count}.")

#────────────────────────────────────────────────────────────────────────
# Step 4: IPS Screening storing statuses
#────────────────────────────────────────────────────────────────────────
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
    st.session_state.setdefault("ips_statuses", {})
    st.subheader("Step 4: IPS Investment Criteria Screening")

    for b in st.session_state.get("fund_blocks", []):
        name = b["Fund Name"]
        statuses = {}
        statuses["Manager Tenure"] = (next((m.get('Status') for m in b['Metrics'] if m['Metric']=="Manager Tenure"), 'Fail')=='Pass')
        for metric in IPS[1:]:
            statuses[metric] = True
        st.session_state["ips_statuses"][name] = statuses
        st.markdown(f"### {name}")
        for m, ok in statuses.items():
            sym = "✅" if ok else "❌"
            st.write(f"- {sym} {m}")

#────────────────────────────────────────────────────────────────────────
# Step 5: Fund Performance Extraction
#────────────────────────────────────────────────────────────────────────
def step5_process_performance(pdf, start_page, fund_names):
    end_page = st.session_state.get("factsheets_page") or (len(pdf.pages)+1)
    all_lines, perf_text = [], ""
    for p in pdf.pages[start_page-1:end_page-1]:
        txt = p.extract_text() or ""
        perf_text += txt + "\n"
        all_lines.extend(txt.splitlines())
    mapping = {}
    for ln in all_lines:
        m = re.match(r"(.+?)\s+([A-Z]{1,5})$", ln.strip())
        if m:
            mapping[re.sub(r'[^A-Za-z0-9 ]+', '', m.group(1)).strip().lower()] = m.group(2)
    tickers = {name: next((t for raw,t in mapping.items() if raw.startswith(re.sub(r'[^A-Za-z0-9 ]','',name).lower())), None) for name in fund_names}
    st.session_state["tickers"] = tickers
    st.subheader("Step 5: Extracted Tickers")
    for n, t in tickers.items(): st.write(f"- {n}: {t or '❌ not found'}")

#────────────────────────────────────────────────────────────────────────
# Step 6: Fund Factsheets Section
#────────────────────────────────────────────────────────────────────────
def step6_process_factsheets(pdf, fund_names):
    st.subheader("Step 6: Fund Factsheets Section")
    start = st.session_state.get("factsheets_page")
    if not start: st.error("Missing factsheets page."); return
    matched = []
    for i in range(start-1, len(pdf.pages)):
        first = " ".join(w['text'] for w in pdf.pages[i].extract_words(use_text_flow=True) if w['top']<100)
        if "Benchmark:" not in first: continue
        ticker = re.search(r"\b([A-Z]{1,5})\b", first)
        ticker = ticker.group(1) if ticker else ""
        best, match_name = 0, ""
        for item in st.session_state.get("fund_blocks", []):
            score = fuzz.token_sort_ratio(f"{first}".lower(), item['Fund Name'].lower())
            if score>best: best, match_name = score, item['Fund Name']
        matched.append({"Fund Name": match_name, "Ticker": ticker, "Matched": best>20})
    st.session_state['fund_factsheets_data'] = matched
    st.dataframe(pd.DataFrame(matched))

#────────────────────────────────────────────────────────────────────────
# Build objects for Step 7 (with numbering)
#────────────────────────────────────────────────────────────────────────
# Build scorecard df with numeric columns 1-14
rows = []
for b in st.session_state.get("fund_blocks", []):
    name = b['Fund Name']
    row = {"Investment Option": name, "Ticker": st.session_state.get("tickers", {}).get(name, "")}
    for idx, m in enumerate(b['Metrics'], start=1):
        row[str(idx)] = m.get('Status', 'Fail')
    rows.append(row)

df_scorecard = pd.DataFrame(rows)

# Build ips_results as before
ips_statuses = st.session_state.get("ips_statuses", {})
first = next(iter(ips_statuses), None)
ips_results = {metric: ('Pass' if ok else 'Fail') for metric, ok in ips_statuses.get(first, {}).items()} if first else {}

st.session_state["scorecard_metrics"] = df_scorecard
st.session_state["ips_screening_results"] = ips_results

#────────────────────────────────────────────────────────────────────────
# Step 7: Display Pass/Fail Tables
#────────────────────────────────────────────────────────────────────────
def step7_create_tables():
    st.subheader("Step 7: Pass/Fail Tables")
    sc = st.session_state.get("scorecard_metrics")
    if sc is None or sc.empty:
        st.warning("No scorecard metrics found.")
    else:
        st.markdown("**Fund Scorecard: Pass/Fail**")
        st.table(sc)

    ips = st.session_state.get("ips_screening_results", {})
    if not ips:
        st.warning("No IPS screening results found.")
    else:
        df2 = pd.DataFrame(ips.items(), columns=["IPS Metric","Result"])
        st.markdown("**IPS Screening Metrics**")
        st.table(df2)

#────────────────────────────────────────────────────────────────────────
# Main driver
def run():
    st.title("IPS Screening & Scorecard")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded: return
    with pdfplumber.open(uploaded) as pdf:
        with st.expander("Step 1: Details", expanded=False):
            process_page1(pdf.pages[0].extract_text() or "")
        with st.expander("Step 2: TOC", expanded=False):
            toc_text = "".join(pdf.pages[i].extract_text() or "" for i in range(min(3,len(pdf.pages))))
            process_toc(toc_text)
        with st.expander("Step 3: Scorecard", expanded=False):
            sp = st.session_state.get('scorecard_page')
            tot = st.session_state.get('total_options')
            if sp and tot is not None:
                step3_process_scorecard(pdf, sp, tot)
            else:
                st.error("Missing scorecard page or total options.")
        with st.expander("Step 4: IPS Screening", expanded=False): step4_ips_screen()
        with st.expander("Step 5: Performance", expanded=False):
            pp = st.session_state.get('performance_page')
            names = [b['Fund Name'] for b in st.session_state.get('fund_blocks', [])]
            if pp and names: step5_process_performance(pdf, pp, names)
            else: st.error("Missing data.")
        with st.expander("Step 6: Factsheets", expanded=False): step6_process_factsheets(pdf, [b['Fund Name'] for b in st.session_state.get('fund_blocks', [])])
        with st.expander("Step 7: Tables", expanded=False): step7_create_tables()

if __name__ == "__main__": run()
