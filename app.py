import sys
import os

# Add repo root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from app_pages import fund_scorecard, user_requests

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FidSync | Fund Management Platform",
    layout="wide"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("FidSync")

page = st.sidebar.radio(
    "Navigation",
    options=[
        "Info: About",
        "Info: How to Use",
        "Tool: Fund Scorecard",
        "Tool: User Requests"
    ],
    format_func=lambda name: name.split(": ")[1]
)

# --- ROUTING ---
if page == "Info: About":
    st.title("About FidSync")
    st.markdown("""
FidSync is an internal platform built to make working with fund documents easier and faster.

Traditionally, updating fund scorecards meant:
- Reading through long PDF investment reports
- Manually copying fund status data
- Finding the correct rows in Excel templates
- Hoping you didn’t miss anything

**FidSync automates that.**  
It extracts key data from reports, fills your Excel templates, and flags Pass/Fail — all in one click.

Questions or requests? Use the **User Requests** tab to reach out.
""")

elif page == "Info: How to Use":
    st.title("How to Use FidSync")
    st.markdown("""
This tool is built for advisors and analysts to quickly update fund scorecards from report PDFs.

---

### 1. Upload Files
Upload:
- A PDF investment report
- An Excel scorecard template

---

### 2. Configure
Enter:
- Sheet name (like `"Scorecard"`)
- Column for status (like `"Status"`)
- Row where the fund list starts
- PDF page range with fund data
- Fund names to match (or let the system detect)

---

### 3. Generate
Click **"Generate Scorecard"** to preview or process the file.

You’ll see results instantly and can download the updated Excel.

---

Need help? Use the **User Requests** tab.
""")

elif page == "Tool: Fund Scorecard":
    fund_scorecard.run()

elif page == "Tool: User Requests":
    user_requests.run()
