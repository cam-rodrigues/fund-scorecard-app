import streamlit as st
import pdfplumber
import pandas as pd
import re

# Build fund-to-ticker lookup table from the entire document
def build_ticker_lookup(pdf):
    fund_to_ticker = {}
    pattern = re.compile(r"(.+?)\s+([A-Z]{4,6}X?)$")

    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.split("\n"):
            match = pattern.match(line.strip())
            if match:
                name = match.group(1).strip()
                ticker = match.group(2).strip()
                fund_to_ticker[name] = ticker
    return fund_to_ticker

# Try fuzzy or partial match if direct match fails
def resolve_ticker(fund_name, lookup):
    for known_name, ticker in lookup.items():
        if known_name.lower() in fund_name.lower() or fund_name.lower() in known_name.lower():
            return ticker
    return "N/A"

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Extracting fund criteria and matching tickers..."):
            criteria_data = []

            with pdfplumber.open(uploaded_file) as pdf:
                # Step 1: Build a ticker lookup table from the whole document
                ticker_lookup = build_ticker_lookup(pdf)

                # Step 2: Go back through and extract fund criteria blocks
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.split("\n")
                        if not lines:
                            continue

                        fund_name = lines[0].strip()
                        ticker = resolve_ticker(fund_name, ticker_lookup)
                        meets_criteria = "placed on watchlist" not in block
                        criteria = []

                        for line in lines[1:]:
                            if line.startswith(("Manager Tenure", "Excess Performance", "Peer Return Rank",
                                                "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
                                                "Sortino Ratio Rank", "Tracking Error Rank")):
                                match = re.match(r"^(.*?)\s+(Pass|Review)(.*?)?$", line.strip())
                                if match:
                                    metric = match.group(1).strip()
                                    result = match.group(2).strip()
                                    criteria.append((metric, result))

                        if criteria:
                            criteria_data.append({
                                "Fund Name": fund_name,
                                "Ticker": ticker,
                                "Meets Criteria": "Yes" if meets_criteria else "No",
                                **{metric: result for metric, result in criteria}
                            })

        if criteria_data:
            df = pd.DataFrame(criteria_data)
            st.success(f"✅ Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download as CSV", data=csv, file_name="fund_criteria_results.csv", mime="text/csv")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
