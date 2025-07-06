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
                font-size: 1.2rem;
                color: #555;
                margin-bottom: 1rem;
            }
        </style>

        <div class="about-card">
            <div class="about-header">Welcome to FidSync</div>
            <div class="about-sub">Your Fund Review Assistant</div>
            <p>
                FidSync helps investment analysts and operations teams extract and validate fund data 
                from PDF reports and generate standardized Excel scorecards.
            </p>
            <p>
                Simply upload your PDF and Excel template, match fund names with investment options,
                and download a clean, formatted scorecard in seconds — without touching formulas.
            </p>
            <hr style="margin: 2rem 0;">
            <p>
                Built for clarity, consistency, and speed. FidSync is your partner in fund evaluation workflows.
            </p>
        </div>
    """, unsafe_allow_html=True)
