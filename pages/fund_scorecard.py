import streamlit as st

# Additional utilities would be imported here

def show():
    st.title("Fund Scorecard Status Tool")
    st.write(
        "Upload your scorecard PDF and workbook, adjust the settings, and run the updater."
    )

    if st.button("Reset"):
        st.experimental_set_query_params(reset="true")
        st.experimental_rerun()

    with st.form("upload_form"):
        with st.expander("Upload Files", expanded=True):
            pdf_file = st.file_uploader("Scorecard PDF", type=["pdf"])
            excel_file = st.file_uploader("Excel Workbook", type=["xlsx", "xlsm"])

        with st.expander("Settings", expanded=True):
            col1, col2, col3 = st.columns(3)
            sheet_name = col1.text_input("Excel Sheet Name")
            status_col = col2.text_input("Starting Column Letter").strip().upper()
            start_row = col3.number_input("Starting Row Number", min_value=1)

            col4, col5 = st.columns(2)
            start_page = col4.number_input("Start Page", min_value=1)
            end_page = col5.number_input("End Page", min_value=1)

            fund_names_input = st.text_area(
                "Investment Option Names (One Per Line)", height=200
            )
            dry_run = st.checkbox(
                "Dry Run (preview only, don't update Excel)", value=False
            )

        submitted = st.form_submit_button("Run Status Update")

    if submitted:
        # Placeholder for real match/update logic
        st.success("Processing complete!")
