import streamlit as st

def run():
    st.title("Capabilities & Potential")

    st.markdown("""
    ### Current Capabilities

    - **Fund Status Analyzer**  
      Automatically matches fund names to plan options and determines compliance using watchlist scoring rules.

    - **Scorecard Visual Markup**  
      Applies conditional formatting (green for Pass, red for Review) directly in Excel exports, supporting audit-ready documentation.

    - **Fuzzy Matching Engine**  
      Handles name variations and minor formatting differences for accurate linking between scorecard PDFs and investment rosters.

    - **Manual Overrides**  
      Allow advisors to adjust fund status or mapping where human context is needed.

    - **Article Analyzer**  
      Summarizes financial news with support for ticker detection, sentiment tagging, table parsing, and PDF exports.

    - **Document Integration Tools**  
      Extracts key metrics from PDF documents using AI-assisted analysis (Sharpe Ratio, Peer Ranking, etc.).

    ---

    ### Future Potential

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
