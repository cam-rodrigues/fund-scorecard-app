import streamlit as st

def run():
    st.markdown("""
        <style>
            .changelog-section {
                background-color: #fdfdfd;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                border-left: 6px solid #1c2e4a;
            }
            .changelog-title {
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 0.75rem;
                color: #1c2e4a;
            }
            .changelog-sub {
                font-size: 1.1rem;
                font-weight: 600;
                margin-top: 1rem;
            }
            .changelog-body {
                font-size: 1rem;
                color: #333;
            }
        </style>

        <div class="changelog-section">
            <div class="changelog-title">Changelog & Feature Plans</div>
            <div class="changelog-body">
                This page includes recent version updates and upcoming planned improvements.
            </div>
        </div>

        <div class="changelog-section">
            <div class="changelog-sub">Version 1.2.0 – July 2025</div>
            <div class="changelog-body">
                <ul>
                    <li>Professional sidebar with styled navigation</li>
                    <li>Unified documentation layout and styling</li>
                    <li>Live fund match preview and improved error handling</li>
                </ul>
            </div>

            <div class="changelog-sub">Version 1.1.0 – June 2025</div>
            <div class="changelog-body">
                <ul>
                    <li>User request form with email validation</li>
                    <li>Fuzzy matching logic upgraded</li>
                    <li>Color-coded Excel output with formula skip detection</li>
                </ul>
            </div>

            <div class="changelog-sub">Version 1.0.0 – May 2025</div>
            <div class="changelog-body">
                <ul>
                    <li>Initial launch with PDF + Excel processing</li>
                    <li>Manual investment option input</li>
                    <li>Basic match results written to Excel</li>
                </ul>
            </div>
        </div>

        <div class="changelog-section">
            <div class="changelog-sub">Planned Features</div>
            <div class="changelog-body">
                <ul>
                    <li>Match confidence scores and review step</li>
                    <li>Multi-sheet Excel support with custom targeting</li>
                    <li>CSV export of preview table</li>
                    <li>Theme toggle (light/dark mode)</li>
                    <li>Admin dashboard for user feedback</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)
