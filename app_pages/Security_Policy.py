import streamlit as st

def run():
    st.markdown("""
        <style>
            .policy-section {
                background-color: #fdfdfd;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                border-left: 6px solid #1c2e4a;
            }
            .policy-title {
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 0.75rem;
                color: #1c2e4a;
            }
            .policy-body {
                font-size: 1rem;
                color: #333;
            }
        </style>

        <div class="policy-section">
            <div class="policy-title">Security & Data Handling</div>
            <div class="policy-body">
                FidSync is designed to meet the standards of internal and enterprise financial workflows. No user data is stored, uploaded, or logged at any point.
            </div>
        </div>

        <div class="policy-section">
            <div class="policy-title">How Your Files Are Handled</div>
            <div class="policy-body">
                <ul>
                    <li>All processing is performed in memory</li>
                    <li>No files are saved to disk or transmitted externally</li>
                    <li>Uploaded files are discarded after processing completes</li>
                </ul>
            </div>
        </div>

        <div class="policy-section">
            <div class="policy-title">Deployment Guidelines</div>
            <div class="policy-body">
                <ul>
                    <li>Use in secure environments (e.g., local workstation or internal network)</li>
                    <li>For public cloud use, add password protection and monitor access logs</li>
                    <li>Review your organization’s compliance policies before deployment</li>
                </ul>
            </div>
        </div>

        <div class="policy-section">
            <div class="policy-title">Data Privacy</div>
            <div class="policy-body">
                FidSync does not collect or process personally identifiable information (PII) by default. All data stays within the runtime environment unless otherwise configured by the deployment team.
            </div>
        </div>
    """, unsafe_allow_html=True)
