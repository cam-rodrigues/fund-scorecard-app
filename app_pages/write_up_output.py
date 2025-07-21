import streamlit as st
import write_up_info  # Make sure write_up_info.py is in the same directory or in PYTHONPATH

def run():
    st.set_page_config(page_title="Step 7: Write-Up Viewer", layout="wide")
    st.title("Step 7: View Write-Up Outputs for Selected Fund")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="writeup_upload")
    if not uploaded_file:
        return

    # Run the full processing pipeline
    write_up_info.run(uploaded_file)

    # Retrieve processed data
    data = write_up_info.get_summary_data()
    fund_blocks = data["fund_blocks"]
    ips_data = data["ips_data"]
    factsheet_data = data["factsheet_data"]

    # Fund selector
    fund_names = [block["Fund Name"] for block in fund_blocks]
    selected_fund = st.selectbox("Select a Fund", fund_names)

    if selected_fund:
        # Get fund block
        fund_block = next((f for f in fund_blocks if f["Fund Name"] == selected_fund), None)
        ips_block = next((i for i in ips_data if i["Fund Name"] == selected_fund), {})
        facts_block = next((f for f in factsheet_data if f["Matched Fund Name"] == selected_fund), {})

        st.subheader(f"Summary for: {selected_fund}")

        # Fund Scorecard Metrics
        st.markdown("### IPS Metrics (Scorecard)")
        st.write({k: v for k, v in ips_block.items() if k != "Fund Name"})

        # Fund Factsheet Info
        st.markdown("### Factsheet Information")
        st.write({k: v for k, v in facts_block.items() if k not in ["Matched Fund Name", "Match Score", "Matched"]})

        # Optionally display Scorecard Metrics too
        st.markdown("### Scorecard Metrics (Raw)")
        st.write(fund_block)

# Required to let Streamlit know this is an app page
if __name__ == "__main__":
    run()
