import streamlit as st
import pdfplumber
import pandas as pd
import re

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Extracting fund criteria..."):
            criteria_data = []
            fund_to_ticker = {}

            # Step 1: Build ticker lookup table from all pages
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    for line in text.split("\n"):
                        # Match lines like: "Vanguard Mid Cap Index Admiral VIMAX"
                        match = re.match(r"^(.*?)([A-Z]{4,6})\s*$", line.strip())
                        if match:
                            fund_name = match.group(1).strip()
                            ticker = match.group(2).strip()
                            fund_to_ticker[fund_name] = ticker

                # Step 2: Parse Fund Scorecard section
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.strip().split("\n")
                        if not lines:
                            continue

                        raw_fund_line = lines[0]
                        # Remove ending like "Fund Meets Watchlist Criteria."
                        clean_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist.*)", "", raw_fund_line).strip()

                        # Fallback to full line if it’s too short after cleanup
                        fund_name = clean_name if len(clean_name.split()) > 2 else raw_fund_line

                        # Try to match fund name to ticker
                        ticker = "N/A"
                        for key in fund_to_ticker:
                            if key.lower() in fund_name.lower():
                                ticker = fund_to_ticker[key]
                                break

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
