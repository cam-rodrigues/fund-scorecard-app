import streamlit as st
from datetime import datetime
from pages import fund_scorecard, user_requests

# ======================
#   PAGE CONFIGURATION
# ======================
st.set_page_config(page_title="FidSync", layout="wide")
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        html, body, [class*='css']  {
            font-family: 'Roboto', sans-serif;
        }
        .block-container {
            padding: 2rem 2rem 2rem 2rem;
            max-width: 1100px;
            margin: auto;
        }
        h1, h2, h3, h4, h5, h6 { color: #003865; font-weight: 700; }
        .stTextInput > label, .stNumberInput > label, .stTextArea > label, .stCheckbox > label {
            font-weight: 500;
        }
        .sidebar-title {
            font-size: 26px !important;
            font-weight: bold;
            color: #003865;
            margin-bottom: 0.25rem;
        }
        .sidebar-section {
            font-size: 14px;
            text-transform: uppercase;
            font-weight: bold;
            margin: 1rem 0 0.5rem 0;
            color: #6c757d;
        }
        .hero-title {
            font-size: 48px;
            font-weight: 700;
            color: #003865;
            margin-bottom: 1rem;
        }
        .stButton > button {
            background: linear-gradient(90deg, #003865 0%, #005399 100%);
            color: white;
            font-size: 18px;
            padding: 0.4rem 1.25rem;
            border-radius: 4px;
            border: none;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #005399 0%, #0070cc 100%);
        }
        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
#   SIDEBAR NAVIGATION
# ======================
st.sidebar.markdown('<div class="sidebar-title">FidSync</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    '<div class="sidebar-section">Navigate</div>', unsafe_allow_html=True
)

page = st.sidebar.radio(
    "",
    ["📖 About FidSync", "🛠 How to Use", "📝 Fund Scorecard", "📋 Requests"],
    label_visibility="collapsed",
)

st.sidebar.caption(f"Version 1.3 • Updated {datetime.today().strftime('%b %d, %Y')}")

# ======================
#   ROUTING
# ======================
if page == "📖 About FidSync":
    st.markdown(
        "<div class='hero-title'>Welcome to FidSync</div>", unsafe_allow_html=True
    )
    st.markdown(
        """
    FidSync is a modern productivity tool designed for investment professionals.
    
    It streamlines repetitive documentation and analysis work, starting with scorecard updates and expanding toward compliance, benchmarking, and more.

    **Key Principles**
    - Clarity: Straightforward inputs, transparent logic
    - Speed: Designed to save hours, not minutes
    - Extensibility: Easy to build on as your workflow grows
    - Professional polish and usability
    """
    )

elif page == "🛠 How to Use":
    st.title("How to Use FidSync")
    st.markdown(
        """
    **📥 Uploads**
    - **Fund Scorecard PDF**: A multi-page document that includes pass/fail indicators for investment options.
    - **Excel Workbook**: The workbook where those statuses will be updated.

    **⚙️ Settings**
    - Sheet name and row where data begins
    - Column where status will be written
    - Start/end page range in the PDF
    - Paste the investment names for matching

    **✅ Process**
    1. Select **Dry Run** to preview results without writing to Excel
    2. Click **Run Status Update** to extract and match
    3. Download your updated workbook or a CSV match log

    ---
    **Example Use Case**
    - PDF contains status results like "Fund Meets Watchlist Criteria"
    - Excel has a row of fund names — you want the tool to find matches and write **Pass/Fail** in a status column

    You can add more tools over time — this app is built to grow.
    """
    )

elif page == "📝 Fund Scorecard":
    fund_scorecard.show()

elif page == "📋 Requests":
    user_requests.show()
