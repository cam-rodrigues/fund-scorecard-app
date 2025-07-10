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

            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    # Split by each fund entry
                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.split("\n")
                        fund_name = lines[0].strip() if lines else "UNKNOWN FUND"
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
