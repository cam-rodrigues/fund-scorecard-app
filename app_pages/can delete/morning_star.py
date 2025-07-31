import re
import streamlit as st
import pdfplumber
from calendar import month_name
import pandas as pd

# === Extractors ===

def extract_overview_fields(text: str) -> dict:
    """Page 1: Fund name, quarter, year, category & benchmark."""
    # Fund name (assumes “Morningstar <Fund Name>” heading)
    m = re.search(r"Morningstar\s+(.+)", text)
    fund_name = m.group(1).strip() if m else None

    # Report date → quarter & year
    m = re.search(r"As of (\d{1,2})/(\d{1,2})/(20\d{2})", text)
    if m:
        mth, day, year = map(int, m.groups())
        q = {(3,31):"1", (6,30):"2", (9,30):"3", (12,31):"4"}.get((mth,day))
        report_quarter = q
        report_year    = str(year)
    else:
        report_quarter = report_year = None

    # Category & Benchmark
    cat = re.search(r"Morningstar Category:\s*(.+)", text)
    bm  = re.search(r"Benchmark:\s*(.+)", text)
    return {
        "fund_name":     fund_name,
        "report_quarter": report_quarter,
        "report_year":    report_year,
        "category":       cat.group(1).strip() if cat else None,
        "benchmark":      bm.group(1).strip()  if bm  else None,
    }

def extract_quarterly_returns(pages: list[str]) -> dict:
    """Find the QTR table and read fund vs benchmark QTD."""
    text = "\n".join(pages)
    lines = text.splitlines()
    # locate header
    idx = next((i for i,ln in enumerate(lines) if "QTR" in ln and "1‑Yr" in ln), None)
    if idx is None or idx+2 >= len(lines):
        return {}
    fund_line = lines[idx+1].split()
    bm_line   = lines[idx+2].split()

    # assume token[1] is QTD
    try:
        f_qtd = fund_line[1]
        b_qtd = bm_line[1]
        diff_bps = int(round((float(f_qtd.strip('%')) - float(b_qtd.strip('%')))*100))
        diff_pct = f"{abs(diff_bps)/100:.2f}%"
    except:
        f_qtd = b_qtd = diff_bps = diff_pct = None

    return {"fund_qtd":f_qtd, "bm_qtd":b_qtd, "diff_bps":diff_bps, "diff_pct":diff_pct}

def extract_top_holding(pages: list[str]) -> dict:
    """Under “Top Holdings”, grab the #1 name, weight & overweight."""
    text = "\n".join(pages)
    m = re.search(r"Top 1 Holding\s+(.+?)\s+([\d\.]+)%\s+\(([\+\-]\d+ bps)\)", text)
    if not m:
        return {}
    name, wt, ov = m.groups()
    return {"top1_name":name.strip(), "top1_wt":wt+"%", "top1_ov":ov}

def extract_manager_info(pages: list[str]) -> dict:
    """Find Lead Manager, start date, tenure years."""
    text = "\n".join(pages)
    m = re.search(r"Lead Manager:\s*([A-Za-z ]+)\s*\(since (\d{1,2}/\d{1,2}/20\d{2})\)", text)
    if not m:
        return {}
    name, start = m.groups()
    # compute tenure in years
    try:
        days = (pd.Timestamp.today() - pd.to_datetime(start)).days
        tenure = f"{days//365} years"
    except:
        tenure = None
    return {"mgr_name":name.strip(), "mgr_start":start, "mgr_tenure":tenure}


# === Main App ===

def run():
    st.title("Morningstar Report Reader")
    uploaded = st.file_uploader("Upload Morningstar PDF", type="pdf")
    if not uploaded:
        return

    # read once
    with pdfplumber.open(uploaded) as pdf:
        pages   = [p.extract_text() or "" for p in pdf.pages]
        overview = extract_overview_fields(pages[0])
        qtr_data = extract_quarterly_returns(pages)
        top1     = extract_top_holding(pages)
        mgr_info = extract_manager_info(pages)

    # Step 1
    with st.expander("Step 1: Overview / Page 1", expanded=True):
        st.write(overview)

    # Step 2
    with st.expander("Step 2: Performance Summary", expanded=False):
        if qtr_data:
            st.write(qtr_data)
        else:
            st.error("Could not parse performance table")

    # Step 3
    with st.expander("Step 3: Top Holdings", expanded=False):
        if top1:
            st.write(top1)
        else:
            st.info("Holdings parsing not yet implemented.")

    # Step 4
    with st.expander("Step 4: Risk Metrics", expanded=False):
        if mgr_info:
            st.write(mgr_info)
        else:
            st.info("Risk‑metric parsing not yet implemented.")

    # Narrative
    with st.expander("Narrative Example", expanded=False):
        if overview and qtr_data:
            arrow = "outperformed" if float(qtr_data["fund_qtd"].strip('%'))>float(qtr_data["bm_qtd"].strip('%')) else "underperformed"
            nth = ["first","second","third","fourth"][int(overview["report_quarter"])-1]
            nm  = overview["fund_name"]
            bm  = overview["benchmark"]
            rpt = f"Q{overview['report_quarter']}, {overview['report_year']}"
            delta = f"{abs(qtr_data['diff_bps'])} bps ({arrow} by {qtr_data['diff_pct']})"
            narrative = f"""
Morningstar Report – MPI

**Fund**  
{nm} {arrow} its benchmark ({bm}) in {rpt} by {delta}.  
The fund’s {arrow} performance was largely due to …  
Going into the quarter the fund allocated {top1.get('top1_wt','')} to {top1.get('top1_name','')}, its top holding, an overweight of {top1.get('top1_ov','')}.  
During lead manager **{mgr_info.get('mgr_name','')}** tenure (since {mgr_info.get('mgr_start','')}), the fund has generally …  
"""
            st.markdown(narrative)
        else:
            st.info("Not enough data to build narrative.")

if __name__ == "__main__":
    run()
