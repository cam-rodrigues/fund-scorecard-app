import streamlit as st

def run():
    st.markdown("""
    <style>
    .card-container {
        display: grid;
        grid-template-columns: 1fr;
        gap: 2.1rem;
        margin-top: 2.2rem;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    .info-card {
        background: #f7fafd;
        border: 1.5px solid #d6e1f3;
        border-radius: 1.6rem;
        box-shadow: 0 2px 12px rgba(66,120,170,0.07);
        padding: 2.1rem 2.6rem 1.4rem 2.6rem;
        margin-bottom: 0.7rem;
        position: relative;
        transition: box-shadow 0.14s;
    }
    .info-card:hover {
        box-shadow: 0 4px 20px rgba(40,70,140,0.10);
        border-color: #aac6e3;
    }
    .info-card h2 {
        margin-top: 0.1em;
        margin-bottom: 0.8em;
        font-size: 1.5rem;
        font-weight: 900;
        color: #164170;
        letter-spacing: -1px;
    }
    .info-card .icon {
        display: inline-block;
        font-size: 1.42rem;
        margin-right: 0.67em;
        vertical-align: middle;
        color: #4578c0;
        font-family: 'Arial Rounded MT Bold', Arial, sans-serif;
    }
    .info-card ul, .info-card ol {
        margin-top: 0.3em;
        margin-bottom: 0.6em;
        padding-left: 1.2em;
    }
    .info-card li {
        margin-bottom: 0.16em;
        font-size: 1.02rem;
    }
    .tips-list {
        list-style-type: "✔️ ";
        padding-left: 1.5em;
        margin-top: 0.4em;
        margin-bottom: 0.4em;
        color: #186638;
        font-size: 1.06rem;
        font-weight: 600;
    }
    .tips-list li {
        margin-bottom: 0.1em;
    }
    .divider {
        margin: 2.2rem 0 1.1rem 0;
        border-top: 1.4px solid #d6e1f3;
    }
    .subtle {
        color: #5e789b;
        font-size: 1.01rem;
        margin-top: 1.1em;
        margin-bottom: 0.5em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <h2><span class="icon">🧰</span>What is FidSync?</h2>
        <div>
            FidSync is a modern toolkit for investment due diligence, fund oversight, and client reporting.<br>
            Built for <b>institutional advisors, plan consultants, and analysts</b>, FidSync combines intelligent document parsing, fund evaluation tools, and data-driven workflows into a unified experience.
        </div>
    </div>

    <div class="info-card">
        <h2><span class="icon">🚦</span>Platform Overview</h2>
        <ul>
            <li><b>Fund Scorecard Tool</b> – Evaluate fund performance against plan options using watchlist criteria and automated status marking (Pass/Review).</li>
            <li><b>Article Analyzer</b> – Summarize financial news with company/ticker detection, sentiment scoring, and exportable insights.</li>
            <li><b>Data Scanner</b> – Extract structured metrics from investment PDFs and Excel files, including peer ranks and risk stats.</li>
            <li><b>Company Lookup</b> – Scan public company websites to collect financial insights, summaries, and disclosures.</li>
        </ul>
    </div>

    <div class="info-card">
        <h2><span class="icon">📝</span>How to Use</h2>
        <ol>
            <li><b>Choose a Tool:</b> Use the sidebar to select a feature. Each module is self-contained and guides you through its workflow.</li>
            <li><b>Upload Required Inputs:</b> Most modules require a PDF, Excel, or a URL. Follow prompts to upload files, paste investment options, or enter search terms.</li>
            <li><b>Review Analysis:</b> FidSync parses your input, extracts content, and surfaces results. See fund names, metrics, scores, and summaries.</li>
            <li><b>Export Your Results:</b> Export data as Excel, CSV, or PDF for documentation or client delivery.</li>
            <li><b>Customize as Needed:</b> Advanced users can override mappings or refine fund matches for higher precision.</li>
        </ol>
    </div>

    <div class="info-card">
        <h2><span class="icon">🔒</span>Data Policy & Security</h2>
        <ul>
            <li>No personal data is ever collected or stored by default.</li>
            <li>All processing is in-memory and files are never saved to disk.</li>
            <li>No uploads are logged or transmitted externally.</li>
            <li>Files are <b>automatically deleted</b> after processing.</li>
        </ul>
    </div>

    <div class="info-card">
        <h2><span class="icon">💡</span>Tips for First-Time Users</h2>
        <ul class="tips-list">
            <li>Use clean, unmodified PDF scorecards or exported Excel files for best results.</li>
            <li>Paste investment options one per line, in Excel order.</li>
            <li>Enable PDF export for print-ready output.</li>
            <li>For articles, prefer reputable sources with structured content.</li>
        </ul>
    </div>

    <div class="info-card">
        <h2><span class="icon">🤝</span>Support & Feedback</h2>
        <div class="subtle">
            FidSync is actively evolving. To report a bug, suggest a feature, or request support, use the <b>User Requests</b> tool in the sidebar.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
