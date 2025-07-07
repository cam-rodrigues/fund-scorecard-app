import streamlit as st

def run():
    st.markdown("""
        <style>
            .manual-section {
                background-color: #fdfdfd;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                border-left: 6px solid #1c2e4a;
            }
            .manual-title {
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: #1c2e4a;
            }
            .manual-body {
                font-size: 1rem;
                color: #333;
            }
        </style>

        <div class="manual-section">
            <div class="manual-title">What Is FidSync?</div>
            <div class="manual-body">
                FidSync is a secure, professional tool for financial teams that need to match fund statuses from PDF scorecards to Excel templates.
                It saves time, reduces manual copy-paste errors, and provides a polished interface for accurate reporting.
            </div>
        </div>

        <div class="manual-section">
            <div class="manual-title">Navigation Overview</div>
            <div class="manual-body">
                Use the left-hand sidebar to access each section of the app:
                <ul>
                    <li><strong>About:</strong> Learn what FidSync does and why it's secure.</li>
                    <li><strong>How to Use:</strong> This page! A guide for getting started.</li>
                    <li><strong>Fund Scorecard:</strong> The core tool — upload your PDF and Excel files, paste your investment options, and generate updates.</li>
                    <li><strong>User Requests:</strong> Submit a feature request or improvement suggestion directly from within the app.</li>
                </ul>
            </div>
        </div>

        <div class="manual-section">
            <div class="manual-title">Security & Confidentiality</div>
            <div class="manual-body">
                All processing happens in memory — no files are stored or uploaded anywhere. FidSync is designed to be safe for use with confidential data
                in a local or enterprise-secured deployment.
            </div>
        </div>

        <div class="manual-section">
            <div class="manual-title">Best Practices</div>
            <div class="manual-body">
                <ul>
                    <li>Paste investment options exactly as they appear in your source, one per line.</li>
                    <li>Preview the results before downloading — you can validate the matching output directly in the app.</li>
                    <li>Use the <strong>User Requests</strong> tab to request improvements. Feedback helps guide development.</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)
