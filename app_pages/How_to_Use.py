import streamlit as st

def run():
    st.markdown("""
        <style>
            .step-card {
                background-color: #fdfdfd;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                border-left: 6px solid #1e88e5;
            }
            .step-title {
                font-size: 1.4rem;
                font-weight: 600;
                margin-bottom: 0.3rem;
            }
            .step-body {
                font-size: 1rem;
                color: #333;
            }
        </style>

        <div class="step-card">
            <div class="step-title">Step 1: Log In</div>
            <div class="step-body">Use the password stored in <code>.streamlit/secrets.toml</code> to unlock the app.</div>
        </div>
        <div class="step-card">
            <div class="step-title">Step 2: Upload Files</div>
            <div class="step-body">You’ll need a PDF fund scorecard, an Excel template, and a list of investment options.</div>
        </div>
        <div class="step-card">
            <div class="step-title">Step 3: Paste Investment Options</div>
            <div class="step-body">Paste them one per line — matching the fund order.</div>
        </div>
        <div class="step-card">
            <div class="step-title">Step 4: Run and Download</div>
            <div class="step-body">Click Run, review matches, and download your updated Excel file.</div>
        </div>
    """, unsafe_allow_html=True)
