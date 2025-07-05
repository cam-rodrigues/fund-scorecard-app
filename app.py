import streamlit as st
from datetime import datetime

# ======================
#   PAGE CONFIG
# ======================
st.set_page_config(page_title="FidSync", layout="wide")

# ======================
#   SIDEBAR NAVIGATION
# ======================
st.sidebar.title("FidSync")
st.sidebar.markdown("---")
st.sidebar.subheader("Navigate")
page = st.sidebar.radio("", ["About FidSync", "How to Use", "Fund Scorecard"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.subheader("Tools")
# Future tools will go here

st.sidebar.caption(f"Version 1.1 • Updated {datetime.today().strftime('%b %d, %Y')}")

# ======================
#   PAGE ROUTING
# ======================
if page == "About FidSync":
    st.title("About FidSync")
    st.markdown("""
FidSync streamlines fund documentation review, automates Excel scorecard updates, and lays the groundwork for upcoming compliance and audit workflows.

**Key Features:**
- Automated fund matching using fuzzy logic
- PDF-to-Excel status updates with conditional formatting
- Future-ready structure for compliance tools, plan comparison, and audit logging
""")

elif page == "How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
**Step-by-step:**
1. Go to **Fund Scorecard** from the sidebar.
2. Upload your scorecard PDF and Excel workbook.
3. Input sheet name, starting row, and column for status.
4. Add each investment name on its own line.
5. Click **Run Status Update** to extract and match.

**Dry Run Option:** See what would change without editing the Excel file.
""")

elif page == "Fund Scorecard":
    from pages import fund_scorecard
