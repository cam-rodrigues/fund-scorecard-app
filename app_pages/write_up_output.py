import streamlit as st
from write_up_info import run as process_writeup_info
import pandas as pd

def run():
    st.set_page_config(page_title="Write-Up Outputs", layout="wide")
    st.title("Write-Up Fund Summary Viewer")

    # === Upload the MPI file and run full processing ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_summary_upload")

    if not uploaded_file:
        st.info("Please upload an MPI PDF to begin.")
        return

    # Re-run all extraction steps
    process_writeup_info()

    # After all data is processed, give dropdown to select a fund
    fund_blocks = st.session_state.get("fund_blocks", [])
    ips_results = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])

    if not fund_blocks or not ips_results or not factsheet_data:
        st.warning("Please make sure the data has been processed successfully.")
        return

    fund_names = [block["Fund Name"] for block in fund_blocks]
    selected_fund = st.selectbox("Select a Fund to View Details", fund_names)

    # Fund Scorecard Metrics
    st.subheader("Fund Scorecard Metrics")
    block = next((b for b in fund_blocks if b["Fund Name"] == selected_fund), None)
    if block:
        df = pd.DataFrame(block["Metrics"])
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No scorecard data found for this fund.")

    # IPS Screening Results
    st.subheader("IPS Screening Result")
    ips_entry = next((entry for entry in ips_results if entry["Fund Name"] == selected_fund), None)
    if ips_entry:
        st.write(f"**Fund Type:** {ips_entry['Fund Type']}")
        st.write(f"**Overall IPS Status:** `{ips_entry['Overall IPS Status']}`")
        st.dataframe(pd.DataFrame(ips_entry["IPS Metrics"]), use_container_width=True)
    else:
        st.write("No IPS result found for this fund.")

    # Factsheet Data
    st.subheader("Factsheet Info")
    facts = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), None)
    if facts:
        display_keys = [
            "Ticker", "Benchmark", "Category", "Net Assets", "Manager Name", "Avg. Market Cap", "Expense Ratio"
        ]
        for key in display_keys:
            st.write(f"**{key}:** {facts.get(key, 'N/A')}")
    else:
        st.write("No factsheet data found for this fund.")
