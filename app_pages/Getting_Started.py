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
                    <li><strong>Getting Started:</strong> You're here — this is the main overview and user guide.</li>
                    <li><strong>Fund Scorecard:</strong> Upload your files and generate your updated Excel report.</li>
                    <li><strong>User Requests:</strong> Suggest improvements, report bugs, or submit feedback.</li>
                    <li><strong>Roadmap:</strong> See what's coming next.</li>
                </ul>
            </div>
        </div>

        <div class="manual-section">
            <div class="manual-title">Security & Confidentiality</div>
            <div class="manual-body">
                All file processing happens in memory — nothing is stored or uploaded. FidSync is safe to use with sensitive internal documents or client data.
            </div>
        </div>

        <div class="manual-section">
            <div class="manual-title">Best Practices</div>
            <div class="manual-body">
                <ul>
                    <li>Paste investment options exactly as they appear in your source — one per line.</li>
                    <li>Review the match preview before downloading to ensure accuracy.</li>
                    <li>Use the <strong>User Requests</strong> tab if you want to see something improved.</li>
                </ul>
            </div>
        </div>

        <div class="manual-section">
            <div class="manual-title">Common Questions</div>
            <div class="manual-body">
                <p><strong>Q: Why can’t I paste directly from Excel?</strong><br>
                A: Excel often includes hidden formatting that breaks the input. Use plain text with one investment per line.</p>

                <p><strong>Q: What do “Pass” and “Fail” mean?</strong><br>
                A: FidSync extracts these status phrases from your PDF. It writes them into your Excel template, color-coded (green/red).</p>

                <p><strong>Q: Is this tool secure?</strong><br>
                A: Yes — it runs in memory and never stores or uploads your data.</p>

                <p><strong>Q: What if my fund names don't match exactly?</strong><br>
                A: FidSync uses fuzzy matching to find the closest possible match. You’ll see a preview before anything is applied.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
