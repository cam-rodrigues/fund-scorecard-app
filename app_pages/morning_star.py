# morningstar_parser.py

import re
import pdfplumber
import pandas as pd

def extract_overview(pdf):
    """
    Grabs from page 1 the Fund Name, Ticker, NAV, NAV change,
    Total Assets, Expense Ratio, Category, Morningstar Rating,
    Analyst name, and Medalist Rating.
    """
    text = pdf.pages[0].extract_text() or ""
    # Fund Name & Ticker
    m = re.search(r'^(.*?)\n.*?Ticker\s*[:\-]?\s*([A-Z]{3,5})', text, re.MULTILINE)
    name, ticker = (m.group(1).strip(), m.group(2)) if m else ("", "")
    # NAV & NAV change
    nav, nav_chg = "", ""
    m = re.search(r'NAV\s+([\d,]+\.\d+)\s+([+\-]\d+\.\d+%)', text)
    if m:
        nav, nav_chg = m.group(1), m.group(2)
    # Total Assets
    m = re.search(r'([\d\.]+)\s*(?:B|M|K)il', text)
    assets = m.group(0) if m else ""
    # Expense Ratio
    m = re.search(r'Adj\.Expense Ratio\s+([\d\.]+%?)', text)
    expense = m.group(1) if m else ""
    # Category & Morningstar Rating (★)
    cat = re.search(r'Category\s+([A-Za-z &\-]+)', text)
    stars = re.search(r'Morningstar.*?(\d) Star', text)
    category = cat.group(1).strip() if cat else ""
    rating   = f"{stars.group(1)}‑star" if stars else ""
    # Analyst & Medalist Rating
    analyst = re.search(r'^(.*?)\nSenior Analyst', text, re.MULTILINE)
    medalist = re.search(r'Morningstar Medalist Rating.*?(\w+)', text)
    return {
        "Fund Name": name,
        "Ticker": ticker,
        "NAV": nav,
        "NAV Change": nav_chg,
        "Total Assets": assets,
        "Expense Ratio": expense,
        "Category": category,
        "Morningstar Rating": rating,
        "Analyst": analyst.group(1).strip() if analyst else "",
        "Medalist Rating": medalist.group(1) if medalist else ""
    }

def extract_returns(pdf):
    """
    Finds the calendar‐year returns table (usually labeled "Returns"
    with years as row or column headers), and returns a DataFrame
    with Fund vs. Category vs. Index for each year.
    """
    # concatenate pages until we've seen "Returns" and year headers
    text = ""
    for p in pdf.pages[:5]:
        text += p.extract_text() + "\n"
    # locate the block starting at “Returns” through a blank line
    lines = text.splitlines()
    start = next(i for i,l in enumerate(lines) if l.strip().startswith("Returns"))
    block = []
    for l in lines[start+1:]:
        if not l.strip():
            break
        block.append(l)
    # parse header years
    header = re.split(r'\s{2,}', block[0].strip())
    years = [h for h in header if re.match(r'\d{4}', h)]
    rows = []
    for l in block[1:]:
        parts = re.split(r'\s{2,}', l.strip())
        if len(parts) >= len(years)+1:
            name = parts[0]
            vals = parts[1:1+len(years)]
            rows.append([name] + vals)
    df = pd.DataFrame(rows, columns=["Name"] + years)
    return df

def extract_mpt_stats(pdf, period="3Yr"):
    """
    Extracts MPT stats (Alpha, Beta, Upside/Downside capture)
    for either 3Yr or 5Yr section.
    """
    target = f"MPT Statistics ({period})"
    # find page
    page_num = next((i for i,p in enumerate(pdf.pages) if target in (p.extract_text() or "")), None)
    if page_num is None:
        return pd.DataFrame()
    lines = pdf.pages[page_num].extract_text().splitlines()
    data = []
    hdr = ["Name","Alpha","Beta","Upside Cap","Downside Cap"]
    for l in lines:
        parts = l.split()
        # look for lines with TICKER (all caps) + four floats
        m = re.match(r'^([A-Za-z &\-]+)\s+([A-Za-z]{3,5})\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)', l)
        if m:
            nm, tk, a, b, u, d = m.groups()
            data.append([f"{nm} ({tk})", a, b, u, d])
    return pd.DataFrame(data, columns=hdr)

def extract_peer_rank(pdf):
    """
    Extracts Peer Ranking % for Sharpe, Sortino, Information
    for 1Yr/3Yr/5Yr/10Yr from the factsheet pages.
    """
    text = ""
    for p in pdf.pages:
        text += p.extract_text() + "\n"
    lines = text.splitlines()
    records = []
    metrics = ["Sharpe Ratio", "Sortino Ratio", "Information Ratio"]
    for fund in re.findall(r'Fund Facts Details for\s+([A-Za-z &\-]+)\s+\(([A-Z]{3,5})\)', text):
        name, tk = fund
        rec = {"Fund": f"{name} ({tk})"}
        for m in metrics:
            # find the line e.g. "Sharpe Ratio / Peer Ranking %"
            idx = next((i for i,l in enumerate(lines) if m in l and "/" in l), None)
            if idx:
                vals = re.findall(r'(\d+\.\d+/\d+)', lines[idx])
                for i,period in enumerate(["3Yr","5Yr","3Yr","5Yr"]):
                    rec[f"{m} {period}"] = vals[i] if i < len(vals) else None
        records.append(rec)
    return pd.DataFrame(records)

def parse_morningstar(path):
    """
    High‐level entry point: open PDF, run all extractors,
    and return a dict of DataFrames / dicts.
    """
    with pdfplumber.open(path) as pdf:
        overview     = extract_overview(pdf)
        returns_yr   = extract_returns(pdf)
        mpt3         = extract_mpt_stats(pdf, "3Yr")
        mpt5         = extract_mpt_stats(pdf, "5Yr")
        peer_ranks   = extract_peer_rank(pdf)
    return {
        "overview": overview,
        "calendar_returns": returns_yr,
        "mpt_3yr": mpt3,
        "mpt_5yr": mpt5,
        "peer_rank": peer_ranks
    }

if __name__ == "__main__":
    import sys
    data = parse_morningstar(sys.argv[1])
    print("== Overview ==")
    for k,v in data["overview"].items():
        print(f"- {k}: {v}")
    print("\n== Calendar Year Returns ==")
    print(data["calendar_returns"].to_string(index=False))
    print("\n== 3Yr MPT Stats ==")
    print(data["mpt_3yr"].to_string(index=False))
    print("\n== Peer Rankings ==")
    print(data["peer_rank"].to_string(index=False))
