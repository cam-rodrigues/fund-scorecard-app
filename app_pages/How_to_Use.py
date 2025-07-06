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
            <div class="step-title">Step 1: Upload Files</div>
            <div class="step-body">
                Upload your fund report PDF and Excel template. The Excel file should include any existing formatting, formulas, or layouts you want preserved.
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 2: Select Page Range</div>
            <div class="step-body">
                Choose the start and end page for the section of the PDF that contains the fund data you want to extract. This narrows the scope and improves accuracy.
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 3: Provide Investment Options</div>
            <div class="step-body">
                Paste your investment options — one per line — in the exact order you'd like them aligned with the PDF data.
                <br><br>
                <strong>Note:</strong> Investment options cannot be extracted from Excel automatically because:
                <ul>
                    <li>They often use formulas instead of plain text (e.g., <code>=A1</code>)</li>
                    <li>Layouts vary (merged cells, scattered rows)</li>
                    <li>Headers may be missing or inconsistent</li>
                </ul>
                <br>
                Use the text box or upload a CSV. You can also paste from clipboard.
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 4: Run the Match</div>
            <div class="step-body">
                Click the <strong>"Run Match"</strong> button to extract fund names, match them to your investment options, and flag any discrepancies.
            </div>
        </div>

        <div class="step-card">
            <div class="step-title">Step 5: Export to Excel</div>
            <div class="step-body">
                Review the results, make any adjustments, and export the cleaned fund scorecard to Excel. Your formatting and template structure will remain intact.
            </div>
        </div>
    """, unsafe_allow_html=True)
