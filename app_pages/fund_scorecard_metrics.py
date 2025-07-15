import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches

# --- Build Fund‑Name ➜ Ticker lookup from all performance pages ---
def build_ticker_lookup(pdf):
    lookup = {}
    last_line = ""
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            # Match lines like "Fidelity Mid Cap Index   FSMDX"
            match = re.match(r"(.+?)\s{2,}([A-Z]{4,6})$", line)
            if match:
                fund, ticker = match.group(1).strip(), match.group(2).strip()
                lookup[fund] = ticker
            else:
                # If ticker is on a separate line below
                if re.match(r"^[A-Z]{4,6}$", line) and last_line:
                    lookup[last_line.strip()] = line.strip()
            last_line = line
    return lookup

# --- Try to extract the fund name from a block using several heuristics ---
def get_fund_name(block, lookup):
    block_lower = block.lower()
    for name in lookup:
        if name.lower() in block_lower:
            return name

    # Heuristic: first 5 lines that are likely titles
    lines = block.split("\n")[:6]
    candidate_lines = [line.strip() for line in lines if sum(c.isupper() for c in line) > 5]

    for line in candidate_lines:
        matches = get_close_matches(line, lookup.keys(), n=1, cutoff=0.6)
        if matches:
            return matches[0]

    matches = get_close_matches(block, lookup.keys(), n=1, cutoff=0.6)
    return matches[0] if matches else "UNKNOWN FUND"

# --- Streamlit App ---
def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if pdf_file:
        rows = []
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            progress = st.progress(0, text="Building ticker lookup...")

            ticker_lookup = build_ticker_lookup(pdf)

            for i, page in enumerate(pdf.pages):
                txt = page.extract_text()
                if not txt:
                    progress.progress((i + 1) / total_pages, text=f"Skipping page {i + 1} (no text)...")
                    continue

                # Try splitting blocks using watchlist phrasing
                blocks = re.split(
                    r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))",
                    txt)

                for block in blocks:
                    if not block.strip():
                        continue

                    fund_name = get_fund_name(block, ticker_lookup)
                    ticker = ticker_lookup.get(fund_name, "N/A")
                    meets = "Yes" if "placed on watchlist" not in block else "No"

                    metrics = {}
                    for line in block.split("\n"):
                        if line.startswith((
                            "Manager Tenure", "Excess Performance", "Peer Return Rank",
                            "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
                            "Sortino Ratio Rank", "Tracking Error Rank")):
                            m = re.match(r"^(.*?)\s+(Pass|Review)", line.strip())
                            if m:
                                metrics[m.group(1).strip()] = m.group(2).strip()

                    if metrics:
                        rows.append({
                            "Fund Name": fund_name,
                            "Ticker": ticker,
                            "Meets Criteria": meets,
                            **metrics
                        })

                progress.progress((i + 1) / total_pages, text=f"Processed page {i + 1} of {total_pages}")

            progress.empty()

        if rows:
            df = pd.DataFrame(rows)
            st.success(f"✅ Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download as CSV",
                                   data=csv,
                                   file_name="fund_criteria_results.csv",
                                   mime="text/csv")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
