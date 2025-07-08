# app_pages/article_analyzer.py

import streamlit as st
import re
import pdfplumber
from io import StringIO

# Try importing newspaper3k (you must add it to requirements.txt)
try:
    from newspaper import Article
except ImportError:
    st.error("Please install newspaper3k: pip install newspaper3k")
    st.stop()

def extract_metrics(text):
    patterns = {
        "EPS": r"EPS[:\s]*\$?([\d.]+)",
        "Revenue": r"Revenue[:\s]*\$?([\d.]+[MB]?)",
        "Market Cap": r"Market\s*Cap(?:italization)?[:\s]*\$?([\d.]+[MB]?)",
    }
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[key] = match.group(1)
    return results

def extract_tickers(text):
    return list(set(re.findall(r"\(([A-Z]{2,5})\)", text)))

def extract_companies(text):
    return list(set(re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)))

def run():
    st.title("📄 Article Analyzer")
    st.markdown("Paste a link, upload a file, or enter raw text to analyze a financial article.")

    input_method = st.radio("Choose input method:", ["Paste URL", "Paste text", "Upload .txt or .pdf"])

    article_text = ""

    if input_method == "Paste URL":
        url = st.text_input("Paste a valid article URL")
        if url:
            try:
                article = Article(url)
                article.download()
                article.parse()
                article_text = article.text
                st.success("Article fetched successfully.")
            except Exception as e:
                st.error(f"Failed to fetch article: {e}")

    elif input_method == "Paste text":
        article_text = st.text_area("Paste your article here", height=300)

    elif input_method == "Upload .txt or .pdf":
        uploaded_file = st.file_uploader("Upload file", type=["txt", "pdf"])
        if uploaded_file:
            if uploaded_file.name.endswith(".txt"):
                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                article_text = stringio.read()
            elif uploaded_file.name.endswith(".pdf"):
                with pdfplumber.open(uploaded_file) as pdf:
                    article_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if article_text.strip():
        st.subheader("📝 Full Text Preview")
        st.write(article_text[:1000] + ("..." if len(article_text) > 1000 else ""))

        st.subheader("📊 Key Metrics")
        metrics = extract_metrics(article_text)
        if metrics:
            for k, v in metrics.items():
                st.write(f"**{k}:** {v}")
        else:
            st.write("No obvious metrics detected.")

        st.subheader("🏢 Companies & Tickers")
        tickers = extract_tickers(article_text)
        companies = extract_companies(article_text)

        st.write("**Tickers:**", ", ".join(tickers) if tickers else "None found.")
        st.write("**Companies:**", ", ".join(companies[:10]) if companies else "None found.")

        st.success("Article analysis complete.")
