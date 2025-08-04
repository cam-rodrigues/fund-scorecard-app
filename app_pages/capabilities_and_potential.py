import streamlit as st

def run():
    st.markdown("""
    <style>
    .card-container {
        display: grid;
        grid-template-columns: 1fr;
        gap: 2.1rem;
        margin-top: 2.2rem;
        max-width: 850px;
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
        font-size: 1.37rem;
        font-weight: 900;
        color: #164170;
        letter-spacing: -1px;
    }
    .info-card ul {
        margin-top: 0.3em;
        margin-bottom: 0.6em;
        padding-left: 1.2em;
    }
    .info-card li {
        margin-bottom: 0.16em;
        font-size: 1.04rem;
        line-height: 1.57;
    }
    .divider {
        margin: 2.2rem 0 1.1rem 0;
        border-top: 1.4px solid #d6e1f3;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <h2>Current Capabilities</h2>
        <ul>
            <li><b>Secure, Ephemeral Processing</b><br>
                All data is handled in memory—no files are stored, and uploads are discarded immediately after use.
            </li>
            <li><b>Invisible Data Cleanup</b><br>
                Automatically strips formulas, formatting residue, and metadata from inputs to ensure consistent downstream results.
            </li>
            <li><b>Context-Aware Parsing</b><br>
                Extracts fund names, metrics, and insights from unstructured PDFs using natural language cues and layout context.
            </li>
            <li><b>Advanced Matching Algorithms</b><br>
                Fuzzy string logic intelligently links records across formats, even with name inconsistencies or formatting errors.
            </li>
            <li><b>Customizable Logic Layers</b><br>
                Supports firm-specific rules for compliance scoring, peer group thresholds, and override workflows.
            </li>
            <li><b>Audit-Ready Output Generation</b><br>
                Creates clean, formatted Excel outputs with embedded status logic, color coding, and no trace of input artifacts.
            </li>
        </ul>
    </div>

    <div class="info-card">
        <h2>Potential</h2>
        <ul>
            <li><b>Benchmark Comparison Tools</b><br>
                Automated comparisons across benchmarks and time periods, with visualization.
            </li>
            <li><b>Portfolio Diagnostics</b><br>
                Risk/return scatterplots, sector exposures, and style box mapping.
            </li>
            <li><b>AI-Driven Recommendations</b><br>
                Insight suggestions based on client IPS documents, plan trends, and peer fund upgrades/downgrades.
            </li>
            <li><b>Enterprise Admin Tools</b><br>
                Role-based access, white-label branding, audit trail logging, and compliance flags.
            </li>
            <li><b>Platform Integrations</b><br>
                Direct sync with custodians (e.g., Fidelity, Schwab), CRMs, and proposal tools.
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
