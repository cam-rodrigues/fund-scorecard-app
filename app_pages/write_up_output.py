# fydsync/app_pages/write_up_outputs.py

import streamlit as st
import pandas as pd
from app_pages.write_up_info import write_up_info  # This must exist as fydsync/app_pages/write_up_info.py

def run():
    st.set_page_config(page_title="Write-Up Fund Info Viewer", layout="wide")
    st.title("Step 7: Fund Detail Viewer")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_step7")
    if not uploaded_file:
        st.warning("Upload an MPI PDF to continue.")
        return

    # Call write_up_info.run with the uploaded file
    write_up_info.run(uploaded_file)

    st.divider()

    fund_blocks = st.session_state.get("fund_blocks", [])
    ips_data = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])

    if not fund_blocks:
        st.warning("No funds found. Make sure the MPI was processed correctly.")
        return

    fund_names = [block["Fund Name"] for block in fund_blocks]
    selected_fund = st.selectbox("Select a Fund", fund_names)

    if not selected_fund:
        return

    # Show Metrics from Scorecard
    st.subheader("Fund Scorecard Metrics")
    scorecard = next((b for b in fund_blocks if b["Fund Name"] == selected_fund), None)
    if scorecard:
        st.dataframe(pd.DataFrame(scorecard["Metrics"]), use_container_width=True)

    # Show IPS Status
    st.subheader("IPS Screening Results")
    ips_entry = next((i for i in ips_data if i["Fund Name"] == selected_fund), None)
    if ips_entry:
        st.write(f"**Fund Type:** {ips_entry['Fund Type']}")
        st.dataframe(pd.DataFrame(ips_entry["IPS Metrics"]), use_container_width=True)
        st.success(f"**Overall IPS Status:** {ips_entry['Overall IPS Status']}")

    # Show Factsheet Details
    st.subheader("Factsheet Summary (If Matched)")
    facts = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), None)
    if facts:
        info = {
            "Ticker": facts["Matched Ticker"],
            "Benchmark": facts["Benchmark"],
            "Category": facts["Category"],
            "Net Assets": facts["Net Assets"],
            "Manager Name": facts["Manager Name"],
            "Avg. Market Cap": facts["Avg. Market Cap"],
            "Expense Ratio": facts["Expense Ratio"]
        }
        st.table(pd.DataFrame(info.items(), columns=["Field", "Value"]))

