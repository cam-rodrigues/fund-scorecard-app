import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(page_title="FidSync", layout="wide")

# Sidebar navigation
st.sidebar.title("FidSync")
st.sidebar.markdown("---")
st.sidebar.subheader("Navigate")
page = st.sidebar.radio("", ["About FidSync", "How to Use", "Fund Scorecard"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption(f"Version 1.1 • Updated {datetime.today().strftime('%b %d, %Y')}")

# Page routing
if page == "About FidSync":
    st.title("About FidSync")
    st.markdown("...")  # existing content

elif page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("...")  # existing content

elif page == "Fund Scorecard":
    from pages.fund_scorecard import show
    show()
