import re
import pdfplumber
from calendar import month_name

def extract_overview_fields(pdf):
    """Page 1: fund name, report date (quarter + year), category, benchmark name."""
    page = pdf.pages[0].extract_text() or ""
    # 1) Fund name
    m = re.search(r"^Morningstar\s+(\S.+)$", page, re.MULTILINE)
    fund_name = m.group(1).strip() if m else None

    # 2) Report date → quarter & year
    m = re.search(r"As of (\d{1,2})/(\d{1,2})/(20\d{2})", page)
    if m:
        mth, day, year = map(int, m.groups())
        q = {(3,31):"1", (6,30):"2", (9,30):"3", (12,31):"4"}.get((mth,day))
        report_quarter = f"{q}"
        report_year    = f"{year}"
    else:
        report_quarter = report_year = None

    # 3) Category & Benchmark
    m_cat = re.search(r"Morningstar Category:\s*(.+)", page)
    category = m_cat.group(1).strip() if m_cat else None
    m_bm = re.search(r"Benchmark:\s*(.+)", page)
    benchmark = m_bm.group(1).strip() if m_bm else None

    return {
        "fund_name": fund_name,
        "report_quarter": report_quarter,
        "report_year": report_year,
        "category": category,
        "benchmark": benchmark,
    }


def extract_quarterly_returns(pdf):
    """Find the 'Quarterly Returns' table, return { 'Fund QTD':…, 'BM QTD':… } in %."""
    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    # find the header line with QTD, 1‑Yr, etc.
    header_rx = re.compile(r"QTR\s+1‑Yr\s+3‑Yr\s+5‑Yr")
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if header_rx.search(ln):
            header_idx = i
            break
    else:
        return {}

    # next two lines: fund and benchmark
    fund_line = lines[header_idx+1].strip()
    bm_line   = lines[header_idx+2].strip()

    # split on whitespace
    tokens_f = fund_line.split()
    tokens_b = bm_line.split()

    # assume first token is name snippet (drop), then QTD is next, benchmark line has no name
    qtd_f   = tokens_f[1]
    qtd_bm  = tokens_b[1]

    # calculate bps difference
    try:
        diff_bps = int(round((float(qtd_f.strip('%')) - float(qtd_bm.strip('%'))) * 100))
        pct_str  = f"{abs(diff_bps)/100:.2f}%"
    except:
        diff_bps = pct_str = None

    return {
        "fund_qtd": qtd_f,
        "bm_qtd":   qtd_bm,
        "diff_bps": diff_bps,
        "diff_pct": pct_str,
    }


def extract_top_holding(pdf):
    """Under 'Top Holdings', grab the #1 name, % weight, and overweight vs bm."""
    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    m = re.search(r"Top 1 Holding\s+(\S.+?)\s+([\d\.]+)%\s+\(([\+\-]\d+\s?bps)\)", text)
    if not m:
        return {}
    name, weight, ov = m.groups()
    return {
        "top1_name": name.strip(),
        "top1_wt":   weight.strip()+"%",
        "top1_ov":   ov.strip(),
    }


def extract_manager_info(pdf):
    """Pull lead manager name, start date, tenure years, etc."""
    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    m = re.search(r"Lead Manager:\s*([A-Za-z ]+)\s*\(since (\d{1,2}/\d{1,2}/20\d{2})\)", text)
    if not m:
        return {}
    name, start = m.groups()
    # approximate end = today
    return {
        "mgr_name": name.strip(),
        "mgr_start": start,
        "mgr_tenure": f"{(pd.Timestamp.now() - pd.to_datetime(start)).days//365} years"
    }


def fill_template(pdf_path):
    import pandas as pd

    with pdfplumber.open(pdf_path) as pdf:
        ovr = extract_overview_fields(pdf)
        qtr = extract_quarterly_returns(pdf)
        top = extract_top_holding(pdf)
        mgr = extract_manager_info(pdf)

    # build narrative
    arrow = "outperformed" if float(qtr["fund_qtd"].strip('%')) > float(qtr["bm_qtd"].strip('%')) else "underperformed"
    narrative = f"""
Morningstar Report – MPI

Fund
{ovr['fund_name']} {arrow} its benchmark in Q{ovr['report_quarter']}, {ovr['report_year']} by {abs(qtr['diff_bps'])} bps ({arrow} by {qtr['diff_pct']}).  
The fund’s {arrow} performance in the {['first','second','third','fourth'][int(ovr['report_quarter'])-1]} quarter was largely due to …  
Going into the quarter the fund allocated {top['top1_wt']} to {top['top1_name']}, its top holding, an overweight of {top['top1_ov']}.  
During lead manager {mgr['mgr_name']} tenure (since {mgr['mgr_start']}), the fund has generally outperformed; his tenure is now {mgr['mgr_tenure']}.  
Action: Consider replacing with …  
"""
    return narrative

if __name__=="__main__":
    print(fill_template("/path/to/Parnassus Core Equity.pdf.pdf"))
