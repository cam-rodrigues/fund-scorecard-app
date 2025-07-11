import streamlit as st
import pdfplumber
import re

# === Config ===
KEY_TERMS = [
    "Sharpe Ratio", "Information Ratio", "Sortino Ratio", "Treynor Ratio",
    "Standard Deviation", "Tracking Error", "Alpha", "Beta", "R²",
    "Expense Ratio", "Manager Tenure", "Net Assets", "Turnover Ratio",
    "Benchmark", "Category", "Calendar Year Returns", "Portfolio Composition",
    "Top 10 Holdings", "Fund Exposures"
]

# === Functions ===
def extract_summary(pdf_file):
    results = []

    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            terms_found = [term for term in KEY_TERMS if term.lower() in text.lower()]
            if terms_found:
                cleaned = re.sub(r'\n+', ' ', text.strip())
                snippet = cleaned[:1500] + "..." if len(cleaned) > 1500 else cleaned
                results.append({
                    "Page": i + 1,
                    "Terms": terms_found,
                    "Snippet": snippet
                })

    return results

# === App ===
def run():
    st.title("🔍 MPI PDF Summary Tool")
    st.markdown("Upload an MPI-style PDF and this tool will summarize the main financial metrics it finds.")

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="summary_pdf")

    if pdf_file:
        with st.spinner("Analyzing document..."):
            summary = extract_summary(pdf_file)

        if summary:
            for section in summary:
                with st.expander(f"Page {section['Page']} — {', '.join(section['Terms'])}"):
                    st.text_area("Excerpt", section["Snippet"], height=300)
        else:
            st.warning("No key financial metrics detected in this PDF.")

