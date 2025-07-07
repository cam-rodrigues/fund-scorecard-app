import streamlit as st

def run():
    st.markdown("""
        <style>
            .about-card {
                background-color: #f9f9f9;
                padding: 2rem;
                border-radius: 16px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                margin-top: 1.5rem;
            }
            .about-header {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }
            .about-sub {
                font-size: 1rem;
                color: #555;
            }
        </style>
        <div class="about-card">
            <div class="about-header">About FidSync</div>
            <div class="about-sub">
                FidSync is a secure, company-branded web app that makes it easy to extract fund statuses from PDF scorecards and sync them into Excel templates.
                <br><br>
                • Secure and confidential (100% in-memory)<br>
                • Built with Python + Streamlit<br>
                • Modern UI and fully brandable for enterprise use
            </div>
        </div>
    """, unsafe_allow_html=True)
