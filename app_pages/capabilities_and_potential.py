import streamlit as st

def run():
    st.markdown("""
    ### Current Capabilities

    - **Secure, Ephemeral Processing**  
      All data is handled in memory—no files are stored, and uploads are discarded immediately after use.

    - **Invisible Data Cleanup**  
      Automatically strips formulas, formatting residue, and metadata from inputs to ensure consistent downstream results.


    - **Context-Aware Parsing**  
      Extracts fund names, metrics, and insights from unstructured PDFs using natural language cues and layout context.

    - **Advanced Matching Algorithms**  
      Fuzzy string logic intelligently links records across formats, even with name inconsistencies or formatting errors.


    - **Customizable Logic Layers**  
      Supports firm-specific rules for compliance scoring, peer group thresholds, and override workflows.


    - **Audit-Ready Output Generation**  
      Creates clean, formatted Excel outputs with embedded status logic, color coding, and no trace of input artifacts.


    ---

    ### Potential

    - **Benchmark Comparison Tools**  
      Automated comparisons across benchmarks and time periods, with visualization.

    - **Portfolio Diagnostics**  
      Risk/return scatterplots, sector exposures, and style box mapping.

    - **AI-Driven Recommendations**  
      Insight suggestions based on client IPS documents, plan trends, and peer fund upgrades/downgrades.

    - **Enterprise Admin Tools**  
      Role-based access, white-label branding, audit trail logging, and compliance flags.

    - **Platform Integrations**  
      Direct sync with custodians (e.g., Fidelity, Schwab), CRMs, and proposal tools.
    """)
