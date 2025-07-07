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
                border-left: 6px solid #1c2e4a;
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
            <div class="step-title">Step 1: Open the Fund Scorecard Tool</div>
            <div class="step-body">Use the sidebar to select <strong>Fund Scorecard</strong>.</div>
        </div>
        <div class="step-card">
            <div class="step-title">Step 2: Upload Files</div>
            <div class="step-body">Upload your PDF fund scorecard and the Excel template file.</div>
        </div>
        <div class="step-card">
            <div class="step-title">Step 3: Paste Investment Options</div>
            <div class="step-body">Paste your investment options — one per line — in the text box provided.</div>
        </div>
        <div class="step-card">
            <div class="step-title">Step 4: Run and Download</div>
            <div class="step-body">Click <strong>Run</strong> to generate results, preview them, and download the updated Excel file.</div>
        </div>
    """, unsafe_allow_html=True)
