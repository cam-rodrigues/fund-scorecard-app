import streamlit as st

def run():
    st.title("Getting Started")

    st.markdown("""
    <style>
        .section {
            background-color: #fdfdfd;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border-left: 6px solid #1c2e4a;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: #1c2e4a;
        }
        .section-body {
            font-size: 1rem;
            color: #333;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section">
        <div class="section-title">What is FidSync?</div>
        <div class="section-body">
            FidSync is a fund alignment tool that reads fund names from a PDF report and updates a formatted Excel template 
            with pass/fail statuses based on your investment options. It’s designed to save time and prevent errors from 
            manual copying and pasting.
        </div>
    </div>

    <div class="section">
        <div class="section-title">What You'll Need</div>
        <div class="section-body">
            <ul>
                <li>A PDF with fund names and statuses</li>
                <li>An Excel template to update</li>
                <li>A list of investment options in plain text (copied from your source system)</li>
            </ul>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Steps Overview</div>
        <div class="section-body">
            <ol>
                <li>Upload the PDF file with fund statuses</li>
                <li>Upload the Excel file you want to update</li>
                <li>Paste or upload your investment options list</li>
                <li>Preview matches</li>
                <li>Download your updated Excel sheet</li>
            </ol>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Why investment options can’t be extracted from Excel</div>
        <div class="section-body">
            Excel often contains:
            <ul>
                <li>Formulas instead of raw text</li>
                <li>Merged cells and inconsistent layouts</li>
                <li>Missing or hidden headers</li>
            </ul>
            Because of that, you’ll need to paste your investment options manually — one per line in the same order as the funds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Common Questions")
    with st.expander("Why can’t I paste directly from Excel?"):
        st.write("Excel often includes hidden formatting that breaks the input. Use plain text with one investment per line.")

    with st.expander("What do “Pass” and “Fail” mean?"):
        st.write("FidSync extracts these status phrases from your PDF. It writes them into your Excel template, color-coded (green/red).")

    with st.expander("Is this tool secure?"):
        st.write("Yes — it runs in memory and never stores or uploads your data.")

    with st.expander("What if my fund names don't match exactly?"):
        st.write("FidSync uses fuzzy matching to find the closest possible match. You’ll see a preview before anything is applied.")
