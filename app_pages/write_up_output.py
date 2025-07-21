import streamlit as st
from app_pages import write_up_info  # This runs and fills session_state
import pandas as pd

def run():
    st.set_page_config(page_title="Fund Info Lookup", layout="wide")
    st.title("Fund Write-Up Output Viewer")

    # === Upload PDF ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="output_pdf")
    if not uploaded_file:
        st.warning("Please upload an MPI PDF.")
        return

    # === Run original processing ===
    st.info("Processing document in background...")
    write_up_info.run(uploaded_file)  # ⬅ pass file directly to function

    # === Wait until fund data is loaded ===
    if "fund_blocks" not in st.session_state or not st.session_state["fund_blocks"]:
        st.error("No fund data found. Please check that the PDF includes the Scorecard section.")
        return

    # === Dropdown for fund selection ===
    fund_names = [block["Fund Name"] for block in st.session_state["fund_blocks"]]
    selected_fund = st.selectbox("Select a fund to view its info:", fund_names)

    # === Lookup info ===
    fund_block = next((f for f in st.session_state["fund_blocks"] if f["Fund Name"] == selected_fund), None)
    perf_data = next((f for f in st.session_state.get("fund_performance_data", []) if f["Fund Scorecard Name"] == selected_fund), {})
    ips_result = next((f for f in st.session_state.get("step8_results", []) if f["Fund Name"] == selected_fund), {})
    factsheet = next((f for f in st.session_state.get("fund_factsheets_data", []) if f["Matched Fund Name"] == selected_fund), {})

    # === Display fund info ===
    st.header(f"📊 Fund: {selected_fund}")

    if perf_data:
        st.subheader("Ticker")
        st.write(perf_data.get("Ticker", "N/A"))

    if factsheet:
        st.subheader("Factsheet Info")
        st.write(f"**Category:** {factsheet.get('Category', 'N/A')}")
        st.write(f"**Benchmark:** {factsheet.get('Benchmark', 'N/A')}")
        st.write(f"**Net Assets:** {factsheet.get('Net Assets', 'N/A')}")
        st.write(f"**Manager Name:** {factsheet.get('Manager Name', 'N/A')}")
        st.write(f"**Avg. Market Cap:** {factsheet.get('Avg. Market Cap', 'N/A')}")
        st.write(f"**Expense Ratio:** {factsheet.get('Expense Ratio', 'N/A')}")

    if ips_result:
        st.subheader("IPS Criteria")
        ips_df = pd.DataFrame(ips_result.get("IPS Metrics", []))
        st.dataframe(ips_df, use_container_width=True)
        st.markdown(f"**Overall IPS Status:** `{ips_result.get('Overall IPS Status', 'N/A')}`")

    if fund_block:
        st.subheader("Raw Fund Scorecard Metrics")
        df = pd.DataFrame(fund_block["Metrics"])
        st.dataframe(df, use_container_width=True)

# Required if running standalone
if __name__ == "__main__":
    run()
