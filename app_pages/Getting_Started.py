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
        .faq-box {
            background-color: #fdfdfd;
            padding: 1.5rem;
            margin-top: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border-left: 6px solid #1c2e4a;
        }
        .faq-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #1c2e4a;
        }
        .faq-question {
            font-size: 1.05rem;
            font-weight: 600;
            margin-top: 1.25rem;
            margin-bottom: 0.25rem;
        }
        .faq-answer {
            font-size: 1rem;
            color: #333;
        }
    </style>

    <div class="manual-section">
        <div class="manual-title">What is FidSync?</div>
        <div class="manual-body">
            FidSync is a fund alignment tool that reads fund names from a PDF report and updates a formatted Excel template 
            with pass/fail statuses based on your investment options. It’s designed to save time and prevent errors from 
            manual copying and pasting.
        </div>
    </div>

    <div class="manual-section">
        <div class="manual-title">What You'll Need</div>
        <div class="manual-body">
            <ul>
                <li>A PDF with fund names and statuses</li>
                <li>An Excel template to update</li>
                <li>A list of investment options in plain text (copied from your source system)</li>
            </ul>
        </div>
    </div>

    <div class="manual-section">
        <div class="manual-title">Steps Overview</div>
        <div class="manual-body">
            <ol>
                <li>Upload the PDF file with fund statuses</li>
                <li>Upload the Excel file you want to update</li>
                <li>Paste or upload your investment options list</li>
                <li>Preview matches</li>
                <li>Download your updated Excel sheet</li>
            </ol>
        </div>
    </div>

    <div class="manual-section">
        <div class="manual-title">Why investment options can’t be extracted from Excel</div>
        <div class="manual-body">
            Excel often contains:
            <ul>
                <li>Formulas instead of raw text</li>
                <li>Merged cells and inconsistent layouts</li>
                <li>Missing or hidden headers</li>
            </ul>
            Because of that, you’ll need to paste your investment options manually — one per line in the same order as the funds.
        </div>
    </div>

    <div class="faq-box">
        <div class="faq-title">Common Questions</div>

        <div class="faq-question">Why can’t I paste directly from Excel?</div>
        <div class="faq-answer">
            Excel often includes hidden formatting that breaks the input. Use plain text with one investment per line.
        </div>

        <div class="faq-question">What do “Pass” and “Fail” mean?</div>
        <div class="faq-answer">
            FidSync extracts these status phrases from your PDF. It writes them into your Excel template, color-coded (green/red).
        </div>

        <div class="faq-question">Is this tool secure?</div>
        <div class="faq-answer">
            Yes — it runs in memory and never stores or uploads your data.
        </div>

        <div class="faq-question">What if my fund names don't match exactly?</div>
        <div class="faq-answer">
            FidSync uses fuzzy matching to find the closest possible match. You’ll see a preview before anything is applied.
        </div>
    </div>
    """, unsafe_allow_html=True)
