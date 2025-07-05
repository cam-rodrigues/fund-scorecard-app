import streamlit as st
from app_pages import fund_scorecard, user_requests

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FidSync",
    layout="wide"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("FidSync")

# Top section: Help & Info
st.sidebar.markdown("**Info**")
info_page = st.sidebar.radio(
    "",
    options=["About", "How to Use"],
    index=0,
    key="info_page"
)

# Divider line
st.sidebar.markdown("---")

# Bottom section: Core tools
st.sidebar.markdown("**Tools**")
tool_page = st.sidebar.radio(
    "",
    options=["Fund Scorecard", "User Requests"],
    index=0,
    key="tool_page"
)

# --- PAGE ROUTING ---

# Info Pages
if info_page == "About":
    st.title("About FidSync")

    st.markdown("""
FidSync is an internal web application built for our team to make working with fund documents easier and faster.

Traditionally, updating fund scorecards means:
- Reading through long PDF investment reports
- Manually copying fund status data
- Finding the correct cells in Excel templates
- Hoping you didn’t miss anything

**FidSync automates all of that.**  
It reads the reports for you, finds the fund statuses, matches them to the right rows in Excel, and color-codes them with Pass/Fail — all in one click.

It’s secure, internal-only, and designed specifically for wealth management workflows like ours.

If you ever have questions, ideas, or issues — use the **User Requests** tab to get support.
""")

elif info_page == "How to Use":
    st.title("How to Use FidSync")

    st.markdown("""
This guide walks you through using the **Fund Scorecard** tool.

---

### Step 1: Upload Files
Upload:
- A **fund report PDF** (usually 2–5 pages)
- An **Excel template** (your firm's scorecard file)

Make sure you're using the correct template — ask your manager if you're not sure.

---

### Step 2: Fill In the Form
Enter:
- The **sheet name** in the Excel file (usually "Scorecard")
- The column name where statuses go (like `"Status"`)
- The **first row** where fund data starts (like row `2`)
- The **page range** in the PDF (where fund info appears)
- The list of **fund names**, one per line (copy from Excel if needed)

> Not sure what to put in? Ask a teammate or submit a question in the **User Requests** tab.

---

### Step 3: Generate Scorecard
Click **"Generate Scorecard"**. The app will:
- Extract the right data from the PDF
- Match it to the fund names in the Excel
- Fill in Pass/Fail with color-coding

If everything looks good, download your updated Excel file.

---

### Need Something Else?
Use the **User Requests** tab to submit feedback or request a new feature.
""")

# Tool Pages
elif tool_page == "Fund Scorecard":
    fund_scorecard.run()

elif tool_page == "User Requests":
    user_requests.run()
