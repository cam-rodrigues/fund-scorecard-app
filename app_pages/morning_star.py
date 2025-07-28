import re
import streamlit as st
import pdfplumber
from calendar import month_name
import pandas as pd

# === Utility: Extract & Label Report Date ===
def extract_report_date(text: str) -> str | None:
    # look for mm/dd/yyyy or quarter ends
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for M, D, Y in dates:
        m, d, y = int(M), int(D), int(Y)
        if (m, d) in [(3,31),(6,30),(9,30),(12,31)]:
            q = { (3,31):"1st", (6,30):"2nd", (9,30):"3rd", (12,31):"4th"}[(m,d)]
            return f"{q} QTR, {y}"
        return f"As of {month_name[m]} {d}, {y}"
    return None

# === Step 1: Cover Page Extraction ===
def process_cover_page(text: str):
    st.subheader("Cover Page")
    date = extract_report_date(text)
    st.write(f"- Report Date: **{date or 'N/A'}**")
    # find fund name / ticker
    m = re.search(r'Fund:\s*(.+?)\s*\((\w+)\)', text or "")
    if m:
        st.write(f"- Fund Name: **{m.group(1).strip()}**")
        st.write(f"- Ticker: **{m.group(2)}**")
    else:
        st.write("_Couldn’t parse Fund Name/Ticker_")

# === Step 2: TOC Parsing ===
def process_toc(text: str):
    st.subheader("Table of Contents")
    # look for common Morningstar sections
    sections = {
        "Summary": r"Fund Summary\s+(\d+)",
        "Performance": r"Performance\s+(\d+)",
        "Holdings": r"Top 10 Holdings\s+(\d+)",
        "Risk": r"Risk Analysis\s+(\d+)",
        "Fees": r"Fees & Expenses\s+(\d+)",
    }
    for label, rx in sections.items():
        m = re.search(rx, text or "")
        st.write(f"- {label}: **{m.group(1) if m else '–'}**")

    # store pages for later
    for k, rx in sections.items():
        m = re.search(rx, text or "")
        st.session_state[f"ms_{k.lower()}_page"] = int(m.group(1)) if m else None

# === Step 3: Summary Bullets Extraction ===
def extract_summary(pdf, page: int):
    st.subheader("Fund Summary")
    if not page:
        st.error("Missing Summary page")
        return
    txt = pdf.pages[page-1].extract_text() or ""
    # grab first 5 bullets
    bullets = [ln for ln in txt.splitlines() if ln.strip().startswith("•")]
    for b in bullets[:5]:
        st.write(b)

# === Step 4: Performance Table ===
def extract_performance(pdf, page: int):
    st.subheader("Performance")
    if not page:
        st.error("Missing Performance page")
        return
    lines = (pdf.pages[page-1].extract_text() or "").splitlines()
    # assume table header contains "YTD", "1 Year", etc.
    header = next((ln for ln in lines if "YTD" in ln and "1 Year" in ln), "")
    cols = header.split()
    data_line = lines[lines.index(header)+1] if header else ""
    vals = re.findall(r"-?\d+\.\d+%", data_line)
    df = pd.DataFrame([vals], columns=cols[: len(vals)])
    st.dataframe(df, use_container_width=True)
    st.session_state["ms_performance"] = df

# === Step 5: Top 10 Holdings ===
def extract_holdings(pdf, page: int):
    st.subheader("Top 10 Holdings")
    if not page:
        st.error("Missing Holdings page")
        return
    table = []
    for ln in pdf.pages[page-1].extract_text().splitlines()[1:11]:
        parts = ln.split()
        # assume last two cols are % and mkt value
        name = " ".join(parts[:-2])
        pct, mkt = parts[-2], parts[-1]
        table.append({"Holding": name, "%": pct, "Market Value": mkt})
    st.table(pd.DataFrame(table))
    st.session_state["ms_holdings"] = table

# === Step 6: Risk Metrics ===
def extract_risk(pdf, page: int):
    st.subheader("Risk Metrics")
    if not page:
        st.error("Missing Risk page")
        return
    txt = pdf.pages[page-1].extract_text() or ""
    # look for Sharpe, Std Dev, Beta
    for metric in ["Sharpe Ratio","Standard Deviation","Beta"]:
        m = re.search(rf"{metric}[:\s]+(-?\d+\.\d+)", txt)
        st.write(f"- {metric}: **{m.group(1) if m else '–'}**")

# === Step 7: Fees & Expenses ===
def extract_fees(pdf, page: int):
    st.subheader("Fees & Expenses")
    if not page:
        st.error("Missing Fees page")
        return
    txt = pdf.pages[page-1].extract_text() or ""
    m = re.search(r"Expense Ratio[:\s]+(\d+\.\d+%)", txt)
    st.write(f"- Expense Ratio: **{m.group(1) if m else '–'}**")

# === Main App ===
def run():
    st.title("Morningstar Report Parser")
    uploaded = st.file_uploader("Upload Morningstar PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # cover
        with st.expander("Step 1: Cover Page", expanded=True):
            process_cover_page(pdf.pages[0].extract_text() or "")

        # TOC
        with st.expander("Step 2: Table of Contents", expanded=False):
            toc_text = "".join(p.extract_text() or "" for p in pdf.pages[:3])
            process_toc(toc_text)

        # Summary
        with st.expander("Step 3: Fund Summary", expanded=False):
            extract_summary(pdf, st.session_state.get("ms_summary_page"))

        # Performance
        with st.expander("Step 4: Performance", expanded=False):
            extract_performance(pdf, st.session_state.get("ms_performance_page"))

        # Holdings
        with st.expander("Step 5: Top 10 Holdings", expanded=False):
            extract_holdings(pdf, st.session_state.get("ms_holdings_page"))

        # Risk
        with st.expander("Step 6: Risk Metrics", expanded=False):
            extract_risk(pdf, st.session_state.get("ms_risk_page"))

        # Fees
        with st.expander("Step 7: Fees & Expenses", expanded=False):
            extract_fees(pdf, st.session_state.get("ms_fees_page"))


if __name__ == "__main__":
    run()
