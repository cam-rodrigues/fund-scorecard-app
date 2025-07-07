import streamlit as st

def run():
    st.markdown("## Security & Data Policy")

    st.markdown("### How FidSync handles your data:")
    st.write("""
    - **In-memory only**: All file processing happens live in memory. No files are saved to disk or uploaded externally.
    - **No cloud dependency**: Unless explicitly deployed, FidSync runs entirely locally or within your secure enterprise environment.
    - **No data logging**: User inputs, uploads, and matches are not stored or logged.
    """)

    st.markdown("### Deployment Considerations")
    st.write("""
    - We recommend using FidSync only on secure workstations or behind a company firewall.
    - For teams using Streamlit Cloud or other deployments, enable app passwords and audit access logs regularly.
    """)

    st.markdown("### GDPR / Compliance Notes")
    st.write("""
    FidSync is compliant with common data privacy standards — no personal data is collected, stored, or transmitted by default.
    Always verify your organization’s policies before processing sensitive content.
    """)
