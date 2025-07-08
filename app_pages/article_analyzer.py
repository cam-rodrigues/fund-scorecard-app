# app_pages/article_analyzer.py

import streamlit as st
import re
from io import StringIO

def run():
    st.title("Article Analyzer")
    st.markdown("Upload or paste a financial article and get a clean summary with key tickers, companies, metrics, and sentiment.")

    option = st.radio("Choose input method:", ["Paste Text", "Upload .txt or .pdf"])

    article_text = ""

    if option == "Paste Text":
        article_text = st.text_area("Paste article text here", height=300)

    elif option == "Upload .txt or .pdf":
        uploaded_file = st.file_uploader("Upload a text or PDF file", type=["txt", "pdf"])
        if uploaded_file:
            if uploaded_file.name.endswith(".txt"):
                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                article_text = stringio.read()
            elif uploaded_file.name.endswith(".pdf"):
                import pdfplumber
                with pdfplumber.open(uploaded_file) as pdf:
                    article_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if article_text:
        st.subheader("📘 Summary")
        st.write(article_text[:1000] + "...")  # Placeholder for now

        # --- Basic Metric Extraction (mock example) ---
        st.subheader("📊 Detected Metrics")
        st.write("🔹 EPS: 2.43\n🔹 Revenue: $3.1B\n🔹 Market Cap: $78B")  # placeholder

        st.subheader("🏷 Tickers & Companies")
        tickers = re.findall(r"\(([A-Z]{2,5})\)", article_text)
        companies = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", article_text)

        st.write("**Tickers**:", set(tickers))
        st.write("**Companies**:", set(companies[:5]))

        st.success("Summary completed — future versions will include PDF export and sentiment scoring.")
