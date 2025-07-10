import streamlit as st

def run():
    st.markdown("""
    FidSync is a modern toolkit for investment due diligence, fund oversight, and client reporting. Built for **institutional advisors, plan consultants, and analysts,** FidSync combines intelligent document parsing, fund evaluation tools, and data-driven workflows into a unified experience.

    ---

    ### Platform Overview

    FidSync **currently** includes the following modules:

    - **Fund Scorecard Tool** – Evaluate fund performance against plan options using watchlist criteria and automated status marking (Pass/Review).
    - **Article Analyzer** – Summarize financial news articles with company/ticker detection, sentiment scoring, and exportable insights.
    - **Data Scanner** – Extract structured performance metrics from investment PDFs and Excel files, including peer ranks and risk stats.
    - **Company Lookup** – Scan public company websites to collect financial insights, summaries, and disclosures.

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

    ### Data Policy & Security
    
    FidSync is designed with privacy in mind:
    
    - It does **not collect or store any personal information** by default.
    - **All data is processed securely in memory** and never saved to disk.
    - **No files are uploaded, logged, or transmitted externally.**
    - Uploaded files are **automatically deleted** once processing is complete.
        
    ---

    ### Tips for First-Time Users

    - Use clean, unmodified PDF scorecards or directly exported Excel files for best results.
    - Always paste investment options one per line (in the order they appear in the Excel).
    - Enable the PDF export feature for print-ready output.
    - When analyzing articles, prefer sources with structured content (e.g. Reuters, CNBC, or Bloomberg).

    ---

    ### Support & Feedback

    FidSync is actively evolving. If you encounter any bugs, have suggestions, or would like to request a feature, please use the **User Requests** tool in the sidebar.
    """)
