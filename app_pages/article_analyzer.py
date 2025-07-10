import streamlit as st
import pdfplumber
import re
import pandas as pd
from newspaper import Article

# === Summarizer stub
def summarize_article(text):
    return text[:1000] + "..." if len(text) > 1000 else text

# === Fund metric extractor
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

# === Main App Logic
def main():
    st.set_page_config(page_title="Article Analyzer", layout="wide")
    st.title("📰 Article Analyzer")
    st.caption("Paste a financial article URL or upload text. Get a summary and detect fund metrics.")

    st.sidebar.header("Options")
    enable_fund_detection = st.sidebar.checkbox("Enable Fund Metric Detection", value=True)

    input_mode = st.radio("Choose Input Method:", ["Paste Article URL", "Paste Text", "Upload PDF"])
    article_text = ""

    if input_mode == "Paste Article URL":
        url = st.text_input("Paste Article URL")
        if url:
            try:
                article = Article(url)
                article.download()
                article.parse()
                article_text = article.text
            except Exception as e:
                st.error(f"Failed to fetch article: {e}")

    elif input_mode == "Paste Text":
        article_text = st.text_area("Paste Article Text", height=300)

    elif input_mode == "Upload PDF":
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                article_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])

    if article_text.strip():
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📝 Summary")
            summary = summarize_article(article_text)
            st.write(summary)

        with col2:
            if enable_fund_detection:
                st.subheader("📊 Detected Fund Metrics")
                metrics_df = extract_fund_metrics(article_text)
                if metrics_df is not None:
                    st.dataframe(metrics_df, use_container_width=True)
                else:
                    st.info("No fund metrics detected.")
            else:
                st.info("Fund detection disabled.")
    else:
        st.info("Paste text, upload a PDF, or enter a URL to begin.")

    st.markdown("""
    ---
    ⚠️ *This tool is for informational purposes only. Metrics may contain errors. Please verify data independently.*
    """)

# === REQUIRED FOR ROUTING ===
def run():
    main()
