import streamlit as st
import pdfplumber
import re
from calendar import month_name
import pandas as pd

# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {year}"
        return f"As of {month_name[m]} {d}, {year}"
    return None

# === Step 1: Extract Fund Scorecard Section ===
def extract_scorecard_blocks(pdf, scorecard_page):
    """Extract all fund blocks and metrics from scorecard section."""
    pages = []
    for p in pdf.pages[scorecard_page-1:]:
        txt = p.extract_text() or ""
        pages.append(txt)
    lines = "\n".join(pages).splitlines()

    metric_labels = [
        "Manager Tenure",
        "Excess Performance (3Yr)",
        "Excess Performance (5Yr)",
        "Peer Return Rank (3Yr)",
        "Peer Return Rank (5Yr)",
        "Expense Ratio Rank",
        "Sharpe Ratio Rank (3Yr)",
        "Sharpe Ratio Rank (5Yr)",
        "R-Squared (3Yr)",
        "R-Squared (5Yr)",
        "Sortino Ratio Rank (3Yr)",
        "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (3Yr)",
        "Tracking Error Rank (5Yr)"
    ]

    fund_blocks = []
    fund_name = None
    metrics = []
    for i, line in enumerate(lines):
        if not any(metric in line for metric in metric_labels) and line.strip():
            if fund_name and metrics:
                fund_blocks.append({"Fund Name": fund_name, "Metrics": metrics})
            fund_name = line.strip()
            fund_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist for not meeting .* out of 14 criteria)", "", fund_name).strip()
            metrics = []
        for metric in metric_labels:
            if metric in line:
                m = re.match(r"^(.*?)\s+(Pass|Review|Fail)\s*(.*)", line.strip())
                if m:
                    metric_name, status, info = m.groups()
                    metrics.append({"Metric": metric_name, "Status": status, "Info": info.strip()})
    if fund_name and metrics:
        fund_blocks.append({"Fund Name": fund_name, "Metrics": metrics})
    return fund_blocks

# === Step 2: IPS Screening ===
def ips_screening(fund_blocks):
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
        "Sharpe Ratio Rank (5Yr)"
    ]
    st.header("IPS Investment Criteria Screening")

    for b in fund_blocks:
        name = b["Fund Name"]
        is_passive = "index" in name.lower()
        statuses, reasons = {}, {}

        info = next((m["Info"] for m in b["Metrics"] if m["Metric"]=="Manager Tenure"), "")
        yrs = float(re.search(r"(\d+\.?\d*)", info).group(1)) if re.search(r"(\d+\.?\d*)", info) else 0
        ok = yrs>=3
        statuses["Manager Tenure"] = ok
        reasons["Manager Tenure"] = f"{yrs} yrs {'≥3' if ok else '<3'}"

        for metric in IPS[1:]:
            m = next((x for x in b["Metrics"] if x["Metric"].startswith(metric.split()[0])), None)
            info = m["Info"] if m else ""
            if "Excess Performance" in metric:
                val_m = re.search(r"([-+]?\d*\.\d+)%", info)
                val = float(val_m.group(1)) if val_m else 0
                ok = (val>0)
                statuses[metric] = ok
                reasons[metric] = f"{val}%"
            elif "R-Squared" in metric:
                pct_m = re.search(r"(\d+\.\d+)%", info)
                pct = float(pct_m.group(1)) if pct_m else 0
                ok = (pct>=95) if is_passive else True
                statuses[metric] = ok
                reasons[metric] = f"{pct}%"
            elif "Peer Return" in metric or "Sharpe Ratio" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                ok = rank<=50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"
            elif "Sortino Ratio" in metric or "Tracking Error" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                if "Sortino" in metric and not is_passive:
                    ok = rank<=50
                elif "Tracking Error" in metric and is_passive:
                    ok = rank<90
                else:
                    ok = True
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"

        fails = sum(not v for v in statuses.values())
        if fails<=4:
            overall="Passed IPS Screen"
        elif fails==5:
            overall="Informal Watch (IW)"
        else:
            overall="Formal Watch (FW)"

        st.markdown(f"### {name} ({'Passive' if is_passive else 'Active'})")
        st.write(f"**Overall:** {overall} ({fails} fails)")
        for m in IPS:
            sym = "✅" if statuses.get(m,False) else "❌"
            st.write(f"- {sym} **{m}**: {reasons.get(m,'—')}")

# === Streamlit App ===
def main():
    st.title("Fidsync IPS Screening Only")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        st.info("Please upload your MPI PDF file.")
        return

    with pdfplumber.open(uploaded) as pdf:
        # Try to auto-locate scorecard page
        toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        sc_match = re.search(r"Fund Scorecard\s+(\d{1,3})", toc_text or "")
        scorecard_page = int(sc_match.group(1)) if sc_match else 3  # fallback to page 3 if not found

        st.info(f"Using Scorecard page: {scorecard_page}")

        fund_blocks = extract_scorecard_blocks(pdf, scorecard_page)
        if not fund_blocks:
            st.error("Could not extract fund scorecard blocks. Check the PDF and page number.")
            return

        ips_screening(fund_blocks)

if __name__ == "__main__":
    main()
