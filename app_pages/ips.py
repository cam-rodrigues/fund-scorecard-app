import re
import streamlit as st
import pdfplumber
import pandas as pd

from calendar import month_name

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Utility: Extract & Label Report Date ===
def extract_report_date(text: str) -> str | None:
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for mon, day, yr in dates:
        m, d, y = int(mon), int(day), yr
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {y}"
        return f"As of {month_name[m]} {d}, {y}"
    return None

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 1: Page 1 Extraction ===
def process_page1(text: str):
    st.subheader("Step 1: Page 1 Metadata")
    report_date = extract_report_date(text)
    if report_date:
        st.session_state['report_date'] = report_date
        st.success(f"Report Date: {report_date}")
    else:
        st.error("Could not detect report date on page 1.")

    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state['total_options'] = int(m.group(1)) if m else None
    st.write(f"- Total Options: {st.session_state['total_options']}")

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 2: Table of Contents Extraction ===
def process_toc(text: str):
    st.subheader("Step 2: Table of Contents Pages")
    sc = re.search(r"Fund Scorecard\s+(\d{1,3})", text or "")
    st.session_state['scorecard_page'] = int(sc.group(1)) if sc else None
    st.write(f"- Fund Scorecard page: {st.session_state['scorecard_page']}")

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 3: Parse Scorecard Blocks (capture Pass/Review) ===
def step3_process_scorecard(pdf, start_page: int, declared_total: int):
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
        m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
        if not m:
            continue
        metric, status, info = m.groups()
        if metric == "Manager Tenure":
            if name and metrics:
                fund_blocks.append({"Fund Name": name, "Metrics": metrics})
            prev = next((lines[j].strip() for j in range(i-1, -1, -1) if lines[j].strip()), "")
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            metrics = []
        if name:
            metrics.append({"Metric": metric, "Status": status, "Info": info.strip()})
    if name and metrics:
        fund_blocks.append({"Fund Name": name, "Metrics": metrics})

    st.session_state["fund_blocks"] = fund_blocks
    st.subheader("Step 3: Scorecard Extraction")
    st.write(f"- Declared: **{declared_total}** funds")
    st.write(f"- Extracted: **{len(fund_blocks)}** funds")
    if len(fund_blocks) == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error("❌ Count mismatch.")

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 3a: Scorecard Metrics → DataFrame (include Pass/Review) ===
def step3_scorecard_table():
    blocks = st.session_state.get("fund_blocks", [])
    if not blocks:
        st.info("No scorecard data. Run Step 3 first.")
        return

    rows = []
    for b in blocks:
        row = {"Investment Options": b["Fund Name"]}
        for m in b["Metrics"]:
            # combine Info and Status
            row[m["Metric"]] = f"{m['Info']} ({m['Status']})"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.subheader("Scorecard Metrics Table")
    st.dataframe(df, use_container_width=True)
    st.session_state["scorecard_df"] = df

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 4a: Build IPS Screening Table ===
def step4_ips_table():
    df_sc = st.session_state.get("scorecard_df")
    tickers = st.session_state.get("tickers", {})
    if df_sc is None:
        st.info("Run Step 3a (Scorecard Table) first.")
        return

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
    ]

    rows = []
    for _, fund in df_sc.iterrows():
        name = fund["Investment Options"]
        row = {
            "Investment Options": name,
            "Ticker": tickers.get(name, "")
        }
        # 1) Manager Tenure ≥3
        tenure_text = fund.get("Manager Tenure", "")
        yrs = float(re.search(r"(\d+\.?\d*)", tenure_text).group(1)) if re.search(r"(\d+\.?\d*)", tenure_text) else 0
        row["1"] = (yrs >= 3)

        # 2–11) other criteria
        for i, crit in enumerate(IPS[1:], start=2):
            raw = fund.get(crit, "")
            if "Excess Performance" in crit:
                val = float(re.search(r"([-+]?\d*\.\d+)%", raw).group(1)) if re.search(r"([-+]?\d*\.\d+)%", raw) else 0
                row[str(i)] = (val > 0)
            elif "R-Squared" in crit:
                row[str(i)] = True
            else:
                rank = int(re.search(r"(\d+)", raw).group(1)) if re.search(r"(\d+)", raw) else 999
                row[str(i)] = (rank <= 50)
        rows.append(row)

    df_ips = pd.DataFrame(rows)
    st.subheader("IPS Screening Results Table")
    st.dataframe(df_ips[["Investment Options","Ticker"] + [str(i) for i in range(1,12)]],
                 use_container_width=True)

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Main App ===
def run():
    st.title("MPI → Scorecard & IPS Tables")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1
        with st.expander("Step 1: Page 1 Metadata", expanded=False):
            process_page1(pdf.pages[0].extract_text() or "")

        # Step 2
        with st.expander("Step 2: Table of Contents", expanded=False):
            toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3,len(pdf.pages))))
            process_toc(toc_text)

        # Step 3
        with st.expander("Step 3: Extract Scorecard Blocks", expanded=False):
            sp = st.session_state.get("scorecard_page")
            tot = st.session_state.get("total_options")
            if sp and tot is not None:
                step3_process_scorecard(pdf, sp, tot)
            else:
                st.error("Missing scorecard page or total options.")

        # Step 3a: show Scorecard Metrics with Pass/Review
        with st.expander("Step 3a: Scorecard Metrics Table", expanded=True):
            step3_scorecard_table()

        # Step 4a: show IPS Screening pass/fail
        with st.expander("Step 4a: IPS Screening Table", expanded=True):
            step4_ips_table()

if __name__ == "__main__":
    run()
