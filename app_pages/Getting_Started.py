import streamlit as st

def run():
    st.markdown("""
    FidSync is a modern toolkit for investment due diligence, fund oversight, and client reporting. Built for institutional advisors, plan consultants, and analysts, FidSync combines intelligent document parsing, fund evaluation tools, and data-driven workflows into a unified experience.

    ---

    ### Platform Overview

    FidSync currently includes the following modules:

    - **Fund Scorecard Tool** – Evaluate fund performance against plan options using watchlist criteria and automated status marking (Pass/Review).
    - **Article Analyzer** – Summarize financial news articles with company/ticker detection, sentiment scoring, and exportable insights.
    - **Document Scanner** – Extract structured performance metrics from investment PDFs and Excel files, including peer ranks and risk stats.
    - **Company Intelligence** – Scan public company websites to collect financial insights, summaries, and disclosures.
    - **Admin & Configuration** – Customize platform settings, monitor usage, and securely manage documents and outputs.

    ---

    ### How to Use FidSync

    **1. Choose a Tool**  
    Navigate using the sidebar to select a feature. Each module is self-contained and provides its own workflow for processing files, articles, or company data.

    **2. Upload Required Inputs**  
    Most modules require a PDF, Excel, or a URL. Follow the prompts on each page to upload documents, paste investment options, or enter search criteria.

    **3. Review Matched Data or Analysis**  
    FidSync parses the input, extracts structured content, and surfaces key results. Where relevant, you'll see fund names, metrics, visual scores, and analysis summaries.

    **4. Export Your Results**  
    Most modules offer export options including Excel, CSV, or PDF — ideal for reporting, documentation, or archiving.

    **5. Customize as Needed**  
    Advanced users can enable manual review, override mappings, or refine fund matches for increased precision.

    ---

    ### Security Policy
    
    FidSync is designed to meet the standards of internal and enterprise financial workflows. No user data is stored, uploaded, or logged at any point. FidSync does not collect or process personally identifiable information (PII) by default. All data stays within the runtime environment unless otherwise configured by the deployment team.
        No files are saved to disk or transmitted externally
        All processing is performed in memory
        Uploaded files are discarded after processing completes
        
    ---

    ### Tips for First-Time Users

    - Use clean, unmodified PDF scorecards or directly exported Excel files for best results.
    - Always paste investment options one per line (in the order they appear in the PDF).
    - Enable the PDF export feature for branded, print-ready output.
    - When analyzing articles, prefer sources with structured content (e.g. Reuters, CNBC, or Bloomberg).
    - If you encounter formatting issues, use the Admin tab to reset inputs or refresh modules.

    ---

    ### Support & Feedback

    FidSync is actively evolving. If you encounter any bugs, have suggestions, or would like to request a feature, please use the feedback option in the sidebar or contact the support team directly.
    """)
