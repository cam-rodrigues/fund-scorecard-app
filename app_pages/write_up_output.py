import streamlit as st
import pandas as pd
import write_up_processor  # Import your processing logic

def run():
    st.set_page_config(page_title="Write-Up Outputs", layout="wide")
    st.title("Step 7: View Write-Up Outputs for Selected Fund")

    # === Get uploaded file from session_state ===
    uploaded_file = st.session_state.get("writeup_upload")

    if not uploaded_file:
        st.warning("Please upload an MPI PDF in the 'Write-Up Info' tab first.")
        return

    # === Only process the MPI if not already done ===
    if "fund_blocks" not in st.session_state:
        write_up_processor.process_mpi(uploaded_file)

    # === Load processed data ===
    fund_blocks = st.session_state.get("fund_blocks", [])
    ips_data = st.session_state.get("step8_results", [])
    factsheet_data = st.session_state.get("fund_factsheets_data", [])

    if not fund_blocks or not ips_data or not factsheet_data:
        st.error("Unable to load processed data. Please try re-uploading the file.")
        return

    # === Dropdown to select fund ===
    fund_names = [block["Fund Name"] for block in fund_blocks]
    selected_fund = st.selectbox("Select a Fund", fund_names)

    st.markdown("---")

    # === Section 1: Fund Scorecard Metrics ===
    st.subheader("1. Fund Scorecard Metrics")
    selected_block = next((b for b in fund_blocks if b["Fund Name"] == selected_fund), None)

    if selected_block:
        df_scorecard = pd.DataFrame(selected_block["Metrics"])
        st.dataframe(df_scorecard, use_container_width=True)
    else:
        st.error("No scorecard metrics found for the selected fund.")

    # === Section 2: IPS Criteria & Status ===
    st.subheader("2. IPS Investment Criteria & Status")
    selected_ips = next((i for i in ips_data if i["Fund Name"] == selected_fund), None)

    if selected_ips:
        st.write(f"**Fund Type:** {selected_ips['Fund Type']}")
        st.write(f"**Overall IPS Status:** `{selected_ips['Overall IPS Status']}`")
        df_ips = pd.DataFrame(selected_ips["IPS Metrics"])
        st.dataframe(df_ips, use_container_width=True)
    else:
        st.warning("No IPS screening data found for the selected fund.")

    # === Section 3: Fund Factsheet Info ===
    st.subheader("3. Fund Factsheet Information")
    selected_fact = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), None)

    if selected_fact:
        st.markdown(f"""
        - **Ticker:** {selected_fact['Matched Ticker']}
        - **Benchmark:** {selected_fact['Benchmark']}
        - **Category:** {selected_fact['Category']}
        - **Net Assets:** {selected_fact['Net Assets']}
        - **Manager Name:** {selected_fact['Manager Name']}
        - **Avg. Market Cap:** {selected_fact['Avg. Market Cap']}
        - **Expense Ratio:** {selected_fact['Expense Ratio']}
        """)
    else:
        st.warning("No factsheet data found for the selected fund.")
