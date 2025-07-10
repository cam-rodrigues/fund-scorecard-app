import streamlit as st
import pdfplumber
import re
import pandas as pd
from newspaper import Article

# === Article Summarizer ===
def summarize_article(text):
    return text[:1000] + "..." if len(text) > 1000 else text

# === Fund Metric Extractor ===
def extract_fund_metrics(text):
    lines = text.splitlines()
    fund_rows = []
    current_fund = None

    for line in lines:
        line = line.strip()
        if re.match(r".+\s[A-Z]{4,6}X", line):
            current_fund = line
            continue
        if current_fund and re.search(r"\d", line) and len(line.split()) >= 6:
            values = re.findall(r"-?\d+\.\d+|\d+", line)
            if values:
                fund_rows.append([current_fund] + values)
                current_fund = None

    if not fund_rows:
        return None

    max_cols = max(len(row) for row in fund_rows)
    columns = ["Fund"] + [f"Metric {i}" for i in range(1, max_cols)]
    return pd.DataFrame(fund_rows, columns=columns)

# === Main Streamlit App ===
def main():
    st.set_page_config(page_title="Article Analyzer", layout="wide")

    st.title("Article Analyzer")
    st.caption("Summarize financial articles and extract potential fund metrics.")

    # Sidebar
    st.sidebar.header("Settings")
    enable_fund_detection = st.sidebar.checkbox("Extract Fund Metrics", value=True)

    # Input Method Dropdown
    input_mode = st.selectbox("Choose Article Input Method", ["Paste URL", "Paste Text", "Upload PDF"])
    article_text = ""

    if input_mode == "Paste URL":
        url = st.text_input("Enter Article URL")
        if url:
            try:
                article = Article(url)
                article.download()
                article.parse()
                article_text = article.text
            except Exception as e:
                st.error(f"Failed to fetch article: {e}")

    elif input_mode == "Paste Text":
        article_text = st.text_area("Paste the Full Article Text Below", height=300)

    elif input_mode == "Upload PDF":
        pdf_file = st.file_uploader("Upload PDF File", type=["pdf"])
        if pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                article_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

    # Process and Display
    if article_text.strip():
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Summary")
            summary = summarize_article(article_text)
            st.write(summary)

        with col2:
            st.subheader("Fund Metrics")
            if enable_fund_detection:
                metrics_df = extract_fund_metrics(article_text)
                if metrics_df is not None:
                    st.dataframe(metrics_df, use_container_width=True)
                else:
                    st.info("No fund metrics were detected.")
            else:
                st.info("Fund metric detection is turned off.")

    else:
        st.info("Please enter text, upload a PDF, or provide a URL to begin analysis.")

    # Disclaimer
    st.markdown("""
    <hr style="margin-top: 2rem; margin-bottom: 1rem;">
    <small><i>This tool is for informational purposes only. Metric accuracy is not guaranteed. Always verify data independently before making investment decisions.</i></small>
    """, unsafe_allow_html=True)

# === Required for Multipage Setup ===
def run():
    main()
