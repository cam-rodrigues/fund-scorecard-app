# write_up_points.py

import pandas as pd
import streamlit as st

def active_passive(*args):
    # Extract data from session state
    fund_data = st.session_state.get("fund_factsheets_data", [])
    performance_data = st.session_state.get("fund_performance_data", [])

    # Create a list to store the rows
    table_data = []

    # Loop through each fund and gather the necessary data
    for fund in fund_data:
        fund_name = fund.get("Matched Fund Name", "N/A")
        benchmark = fund.get("Benchmark", "N/A")
        
        # Extract performance metrics
        perf_item = next((p for p in performance_data if p.get("Fund Scorecard Name") == fund_name), {})
        expense_ratio = perf_item.get("Net Expense Ratio", "N/A")
        turnover_ratio = perf_item.get("Turnover Ratio", "N/A")
        tracking_error = perf_item.get("Tracking Error", "N/A")
        r_squared = perf_item.get("R-Squared", "N/A")
        
        # Append the data to the list
        table_data.append([fund_name, benchmark, expense_ratio, turnover_ratio, tracking_error, r_squared])

    # Create DataFrame
    df = pd.DataFrame(table_data, columns=["Investment Option Name", "Benchmark Name", "Expense Ratio", 
                                           "Turnover Ratio", "Tracking Error", "R-Squared"])

    # Display the table
    st.dataframe(df, use_container_width=True)
