import streamlit as st
from pages import About_FidSync, How_to_Use, fund_scorecard

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="FidSync",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === LOGO + HEADER ===
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="https://i.imgur.com/VB0K4JG.png" alt="FidSync Logo" width="48"/>
        <h1 style="margin-bottom: 0;">FidSync</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# === SIDEBAR NAVIGATION ===
st.sidebar.title("📘 Navigation")
page = st.sidebar.radio("Go to", ["About FidSync", "How to Use", "Fund Scorecard"])

# === RENDER SELECTED PAGE ===
if page == "About FidSync":
    About_FidSync.run()
elif page == "How to Use":
    How_to_Use.run()
elif page == "Fund Scorecard":
    fund_scorecard.run()
