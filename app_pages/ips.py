# step12_viewer.py
import streamlit as st
import pandas as pd

st.title("Fund Facts (Step 12)")

# grab whatever was stored under that key
records = st.session_state.get("step12_fund_facts_table")

if not records:
    st.warning("No data found. Please run Step 12 in your main app first.")
else:
    # turn it into a DataFrame and display
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)
