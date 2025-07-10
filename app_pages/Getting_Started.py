import streamlit as st

st.title("Getting Started")

st.markdown("""
FidSync is a professional-grade platform designed to streamline investment research, fund screening, and portfolio oversight. Our tools help advisors, analysts, and institutions evaluate fund performance, monitor watchlist compliance, and maintain client portfolios with accuracy and ease.

### Step-by-Step Overview

**1. Upload Your Files**  
Upload your fund scorecard (PDF) and metrics spreadsheet (Excel). These are typically quarterly reports received from investment platforms or data vendors.

**2. Enter Investment Options**  
Due to formatting inconsistencies in source files, investment options must be entered manually. Paste them in the order they appear on the scorecard — one per line. CSV upload is also supported.

**3. Match & Analyze**  
Our system performs intelligent matching between fund names and investment options, evaluates them against embedded scoring criteria, and flags status (Pass/Review) using color-coded feedback.

**4. Review & Export**  
Review results directly in the interface. Optionally, export the results to Excel or PDF for recordkeeping or presentation purposes.
""")
