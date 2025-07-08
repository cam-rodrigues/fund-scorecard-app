import streamlit as st
from newspaper import Article
from fpdf import FPDF
from textblob import TextBlob
from dateutil import parser as date_parser
import re
import tempfile
import urllib.parse
from collections import Counter
from datetime import datetime

# === Helpers ===
def safe(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def get_domain(url):
    return urllib.parse.urlparse(url).netloc.replace("www.", "")

def score_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    return "Positive" if polarity > 0.1 else "Negative" if polarity < -0.1 else "Neutral"

def detect_tickers_and_companies(text):
    tickers = re.findall(r'\$?[A-Z]{2,5}(?:\.[A-Z])?', text)
    tickers = list(set([t.strip("$") for t in tickers if 2 <= len(t.strip("$")) <= 6]))
    doc = nlp(text)
    companies = sorted(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
    return tickers, companies

def extract_metrics(text):
    lines = text.split('\n')
    keywords = ["revenue", "growth", "net income", "guidance", "eps", "margin"]
    return [line.strip() for line in lines if any(k in line.lower() for k in keywords) and re.search(r'\d', line)][:5]

def summarize_article(text, max_points=5):
    paras = [p.strip() for p in text.split("\n") if len(p.strip()) > 60]
    all_sentences = []
    freq = Counter(re.findall(r'\w+', text.lower()))
    stopwords = set("the and a to of in that is on for with as this by an be are or it from at was but we not have".split())
    freq = Counter(w for w in freq if w not in stopwords)

    for i, para in enumerate(paras):
        boost = 1.5 if i in [0, len(paras)-1] else 1.0
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for s in sentences:
            score = sum(freq.get(w.lower(), 0) for w in re.findall(r'\w+', s)) * boost
            all_sentences.append((s, score))
    top = sorted(all_sentences, key=lambda x: x[1], reverse=True)
    main = top[0][0] if top else "No summary found."
    bullets = [s for s, _ in top[1:max_points+1]]
    return main, bullets

def fetch_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        title = article.title or "Untitled"
        text = article.text
        date = article.publish_date
        if not date:
            match = re.search(r'(Published|Updated):?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
            if match:
                date = date_parser.parse(match.group(2))
        return title, text, date, article.authors
    except Exception as e:
        return None, f"[Error] {e}", None, []

# === PDF export ===
def export_pdf(summaries):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Finance Article Digest" if len(summaries) > 1 else "Finance Article Summary", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, datetime.now().strftime("%B %d, %Y"), ln=True, align='C')
    pdf.ln(5)

    for i, art in enumerate(summaries, 1):
        pdf.set_font("Arial", 'B', 13)
        pdf.multi_cell(0, 8, f"{i}. {safe(art['title'])}")
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, f"Date: {art['date']} | Source: {art['source']}", ln=True)
        pdf.cell(0, 8, f"Author: {art['author']}", ln=True)
        pdf.cell(0, 8, f"Sentiment: {art['sentiment']}", ln=True)
        pdf.ln(2)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 7, safe("Summary: " + art['summary']))
        if art['points']:
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 7, "Key Points:", ln=True)
            pdf.set_font("Arial", '', 11)
            for pt in art['points']:
                pdf.multi_cell(0, 7, "- " + safe(pt))
        if art['metrics']:
            pdf.ln(1)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 7, "Metrics:", ln=True)
            pdf.set_font("Arial", '', 11)
            for m in art['metrics']:
                pdf.multi_cell(0, 7, "- " + safe(m))
        if art['tickers'] or art['companies']:
            pdf.ln(1)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 7, "Mentions:", ln=True)
            pdf.set_font("Arial", '', 11)
            if art['tickers']:
                pdf.multi_cell(0, 7, "Tickers: " + ", ".join(art['tickers']))
            if art['companies']:
                pdf.multi_cell(0, 7, "Companies: " + ", ".join(art['companies']))
        pdf.ln(5)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# === Streamlit App ===
def run():
    st.title("📊 Article Analyzer")
    st.write("Summarize finance articles, extract sentiment, tickers, and key metrics. Enter one or two article URLs.")
    st.info("Disclaimer: Auto-generated summaries may not be 100% accurate. Always verify with the full article.")

    daily_digest = st.toggle("Daily Digest Mode", value=False)
    depth = st.slider("Summary Depth (number of bullet points)", 3, 10, 5)

    urls = [st.text_input("Article URL 1")]
    if daily_digest:
        urls.append(st.text_input("Article URL 2"))

    if st.button("Analyze Articles"):
        summaries = []
        for i, url in enumerate(urls):
            if not url.strip():
                st.warning(f"Missing URL for article {i+1}")
                return
            with st.spinner(f"Fetching Article {i+1}..."):
                title, text, date, authors = fetch_article(url)
                if text.startswith("[Error]"):
                    st.error(text)
                    return
                summary, points = summarize_article(text, depth)
                tickers, companies = detect_tickers_and_companies(text)
                sentiment = score_sentiment(summary)
                metrics = extract_metrics(text)
                summaries.append({
                    "title": title,
                    "date": date.strftime("%B %d, %Y") if date else "N/A",
                    "summary": summary,
                    "points": points,
                    "metrics": metrics,
                    "tickers": tickers,
                    "companies": companies,
                    "sentiment": sentiment,
                    "source": get_domain(url),
                    "author": ', '.join(authors) if authors else "Unknown"
                })

        for art in summaries:
            st.subheader(art['title'])
            st.markdown(f"**Date:** {art['date']}  \n**Source:** {art['source']}")
            st.markdown(f"**Author:** {art['author']}  \n**Sentiment:** {art['sentiment']}")
            st.markdown(f"**Summary:** {art['summary']}")
            if art['points']:
                st.markdown("**Key Points:**")
                for pt in art['points']:
                    st.markdown(f"- {pt}")
            if art['metrics']:
                st.markdown("**Notable Metrics:**")
                for m in art['metrics']:
                    st.markdown(f"- {m}")
            if art['tickers'] or art['companies']:
                st.markdown("**Mentions:**")
                if art['tickers']:
                    st.markdown(f"Tickers: {', '.join(art['tickers'])}")
                if art['companies']:
                    st.markdown(f"Companies: {', '.join(art['companies'])}")
            st.markdown("---")

        pdf = export_pdf(summaries)
        with open(pdf, "rb") as f:
            st.download_button("📄 Download PDF Summary", f, file_name="article_summary.pdf")

