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
                FidSync is designed to help investment analysts, advisors, and operations professionals
                efficiently process and evaluate mutual fund data.
            </p>
            <p>
                Upload fund PDF reports, match them against your investment options, and output a clean Excel scorecard 
                — all in a few clicks, without dealing with messy formulas or formatting.
            </p>
            <hr style="margin: 2rem 0;">
            <p>
                Whether you're running due diligence, preparing for investment committee reviews, or just need to keep 
                your documentation consistent, FidSync ensures you're ready — fast, clean, and error-free.
            </p>
        </div>
    """, unsafe_allow_html=True)
