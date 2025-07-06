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
                color: #1e88e5;
            }
            .step-body {
                font-size: 1.05rem;
                color: #333;
                line-height: 1.6;
            }
        </style>

        <div class="step-card">
            <div class="step-title">Step 1: Upload Your Files</div>
            <div class="step-body">
                Upload the PDF fund report and your Excel template with existing formatting.
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 2: Select PDF Page Range</div>
            <div class="step-body">
                Choose start and end pages where fund names appear in the PDF report.
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 3: Enter Investment Options</div>
            <div class="step-body">
                Paste or upload a CSV of investment options in the order they should align with the PDF.
                <br><br>
                <strong>Note:</strong> We do not extract investment names from Excel because:
                <ul>
                    <li>Cells may contain formulas (e.g., <code>=A1</code>)</li>
                    <li>Structure varies across sheets</li>
                    <li>Headers may be missing or inconsistent</li>
                </ul>
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 4: Match + Export</div>
            <div class="step-body">
                Run the matcher to align fund names with your options. View pass/fail results and export to Excel or CSV.
            </div>
        </div>
    """, unsafe_allow_html=True)
