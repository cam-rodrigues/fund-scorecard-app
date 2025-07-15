import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# --- Helper: build Fund‑Name ➜ Ticker lookup from the performance tables ---
def build_ticker_lookup(pdf):
    lookup = {}
    pattern = re.compile(r"(.+?)\s+([A-Z]{4,6}X?)$")   # e.g. “Vanguard Mid Cap Index Admiral  VIMAX”
    for page in pdf.pages:
        txt = page.extract_text()
        if not txt:
            continue
        for line in txt.split("\n"):
            m = pattern.match(line.strip())
            if m:
                lookup[m.group(1).strip()] = m.group(2).strip()
    return lookup

# --- Helper: find the correct Fund Name within a criteria block ---
def get_fund_name(block, lookup):
    for name in lookup:
        if name.lower() in block.lower():
            return name
    return "UNKNOWN FUND"

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if pdf_file:
        with st.spinner("Extracting fund criteria and matching tickers…"):
            rows = []

            with pdfplumber.open(pdf_file) as pdf:
                ticker_lookup = build_ticker_lookup(pdf)

                for page in pdf.pages:
                    txt = page.extract_text()
                    if not txt or "Fund Scorecard" not in txt:
                        continue

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

        if rows:
            df = pd.DataFrame(rows)
            st.success(f"Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                # CSV export
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download as CSV",
                                   data=csv,
                                   file_name="fund_criteria_results.csv",
                                   mime="text/csv")

                # Excel export
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Fund Criteria")
                st.download_button("Download as Excel",
                                   data=excel_buffer.getvalue(),
                                   file_name="fund_criteria_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
