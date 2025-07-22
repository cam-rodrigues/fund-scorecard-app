import streamlit as st
import pandas as pd
from app_pages.write_up_processor import write_up_processor

def run():
    st.set_page_config(page_title="Fund IPS Summary", layout="wide")
    st.title("Upload MPI & View Fund IPS Summary")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")

    if not uploaded_file:
        st.warning("Please upload an MPI PDF to continue.")
        return

    if "fund_blocks" not in st.session_state:
        write_up_processor.process_mpi(uploaded_file)
        st.success("File processed.")

    # Load required data
    ips_results = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])
    quarter = st.session_state.get("report_quarter", "Unknown")

    if not ips_results or not factsheet_data:
        st.error("Missing processed data.")
        return

    # === Section 1: Show Full Table for All Funds ===
    st.subheader("Full IPS Summary Table (All Funds)")
    all_rows = []

    for result in ips_results:
        fund_name = result["Fund Name"]
        ips_status = result["Overall IPS Status"]
        metric_results = [m["Status"] if m["Status"] in ("Pass", "Review") else "N/A" for m in result["IPS Metrics"]]
        metric_results = metric_results[:11] + ["N/A"] * (11 - len(metric_results))

        # Match factsheet data
        fund_fact = next((f for f in factsheet_data if f["Matched Fund Name"] == fund_name), {})
        category = fund_fact.get("Category", "N/A")
        ticker = fund_fact.get("Matched Ticker", "N/A")

        row = {
            "Fund Name": fund_name,
            "Ticker": ticker,
            "Category": category,
            "Time Period": quarter,
            "Plan Assets": "$"
        }
        for i in range(11):
            row[f"{i + 1}"] = metric_results[i]
        row["IPS Status"] = ips_status
        all_rows.append(row)

    df_all = pd.DataFrame(all_rows)
    st.dataframe(df_all, use_container_width=True)
