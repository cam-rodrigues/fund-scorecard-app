import streamlit as st
import pdfplumber
import pandas as pd
import re

# Build fund-to-ticker lookup
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

# Improved inception date extraction: scans 5 lines above each match for a known fund name
def build_inception_lookup(pdf, ticker_lookup):
    fund_to_inception = {}
    pattern = re.compile(r"Inception Date:\s*(\d{2}/\d{2}/\d{4})")

    for page in pdf.pages:
        lines = page.extract_text().split("\n") if page.extract_text() else []
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                for j in range(max(0, i - 5), i):
                    for known_name in ticker_lookup:
                        if known_name.lower() in lines[j].lower():
                            fund_to_inception[known_name] = match.group(1)
                            break
    return fund_to_inception

# Match fund name from block to known names
def extract_fund_name_from_block(block, ticker_lookup):
    for known_name in ticker_lookup:
        if known_name.lower() in block.lower():
            return known_name
    return "UNKNOWN FUND"

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Extracting fund criteria, tickers, and inception dates..."):
            criteria_data = []

            with pdfplumber.open(uploaded_file) as pdf:
                ticker_lookup = build_ticker_lookup(pdf)
                inception_lookup = build_inception_lookup(pdf, ticker_lookup)

                for page in pdf.pages:
                    text = page.extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.split("\n")
                        if not lines:
                            continue

                        fund_name = extract_fund_name_from_block(block, ticker_lookup)
                        ticker = ticker_lookup.get(fund_name, "N/A")
                        inception = inception_lookup.get(fund_name, "N/A")
                        meets_criteria = "placed on watchlist" not in block
                        criteria = []

                        for line in lines:
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
                                "Inception Date": inception,
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
