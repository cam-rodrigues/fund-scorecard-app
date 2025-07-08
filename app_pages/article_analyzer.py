from textwrap import dedent
from ace_tools import display_dataframe_to_user

# Re-define since code state was reset
article_analyzer_script = dedent("""
import streamlit as st
import re
import os
import tempfile
import urllib.parse
from collections import Counter
from datetime import datetime
from dateutil import parser as date_parser
from newspaper import Article
from fpdf import FPDF
from textblob import TextBlob
import spacy

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    st.error("❌ SpaCy model 'en_core_web_sm' not available. Check requirements.txt.")
    st.stop()

def safe(text):
    return text.encode("latin-1", "replace").decode("latin-1")

def get_domain(url):
    try:
        return urllib.parse.urlparse(url).netloc.replace("www.", "")
    except:
        return "Unknown"

def score_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    return "Neutral"

def detect_tickers_and_companies(text):
    tickers = re.findall(r'\\$?[A-Z]{2,5}(?:\\.[A-Z])?', text)
    tickers = list(set([t.strip("$") for t in tickers if 2 <= len(t.strip("$")) <= 6]))
    doc = nlp(text)
    companies = sorted(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
    return sorted(set(tickers)), companies

def extract_metrics(text):
    lines = text.split("\\n")
    metrics = []
    for line in lines:
        if any(k in line.lower() for k in ["eps", "revenue", "growth", "net income", "guidance", "margin"]):
            if re.search(r'\\d', line):
                metrics.append(line.strip())
    return metrics[:5]

def summarize_article(text, max_points=5):
    paragraphs = [p.strip() for p in text.split("\\n") if len(p.strip()) > 60]
    all_sentences, quotes, numbers = [], [], []

    words = re.findall(r'\\w+', text.lower())
    stopwords = set(["the", "and", "a", "to", "of", "in", "that", "is", "on", "for", "with", "as", "this", "by", "an", "be", "are", "or", "it", "from", "at", "was", "but", "we", "not", "have", "has", "you", "they", "their", "can", "if", "will", "about"])
    freq = Counter(w for w in words if w not in stopwords)
    signal_phrases = ["according to", "in conclusion", "experts say", "overall", "key finding"]

    for i, para in enumerate(paragraphs):
        sentences = re.split(r'(?<=[.!?])\\s+', para)
        para_boost = 1.5 if i == 0 or i == len(paragraphs) - 1 else 1.0
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 40:
                continue
            base = sum(freq.get(w.lower(), 0) for w in re.findall(r'\\w+', sent))
            bonus = 3 if any(p in sent.lower() for p in signal_phrases) else 0
            score = base * para_boost + bonus
            all_sentences.append((sent, score))
            if re.search(r'[“”"]', sent): quotes.append(sent)
            if re.search(r'\\d', sent): numbers.append(sent)

    sorted_sents = sorted(all_sentences, key=lambda x: x[1], reverse=True)
    main = sorted_sents[0][0] if sorted_sents else "No clear summary found."
    bullets = [s for s, _ in sorted_sents[1:max_points + 1]]
    facts = list(dict.fromkeys(quotes + numbers))[:3]
    return main, bullets, facts, freq

def fetch_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        title = article.title
        text = article.text
        pub_date = article.publish_date
        if not pub_date:
            match = re.search(r'(Published|Updated)[:\\s]+([A-Za-z]+\\s+\\d{1,2},\\s+\\d{4})', text)
            if match:
                pub_date = date_parser.parse(match.group(2))
        return title, text, pub_date, article.authors
    except Exception as e:
        return None, f"[Error] {e}", None, []

def generate_pdf_digest(summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, safe("Finance Article Summary"), ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, safe(datetime.now().strftime("%B %d, %Y")), ln=True, align='C')
    pdf.ln(10)

    for i, article in enumerate(summaries, 1):
        pdf.set_font("Arial", 'B', 14)
        pdf.multi_cell(0, 10, safe(f"{i}. {article['title']}"))
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, safe(f"Published: {article['date']} | Source: {article['source']}"), ln=True)
        if article["author"]:
            pdf.cell(0, 8, safe(f"Author: {article['author']}"), ln=True)
        pdf.cell(0, 8, f"Sentiment: {article['sentiment']}", ln=True)
        pdf.ln(2)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Summary:", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 8, safe(article["summary"]))
        pdf.ln(2)

        if article["key_points"]:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Key Points:", ln=True)
            pdf.set_font("Arial", '', 12)
            for pt in article["key_points"]:
                pdf.multi_cell(0, 8, safe(f"- {pt}"))
            pdf.ln(1)

        if article["metrics"]:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Notable Metrics:", ln=True)
            pdf.set_font("Arial", '', 12)
            for line in article["metrics"]:
                pdf.multi_cell(0, 8, safe(f"- {line}"))
            pdf.ln(1)

        if article["tickers"] or article["companies"]:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Mentions:", ln=True)
            pdf.set_font("Arial", '', 12)
            if article["tickers"]:
                pdf.multi_cell(0, 8, safe(f"Tickers: {', '.join(article['tickers'])}"))
            if article["companies"]:
                pdf.multi_cell(0, 8, safe(f"Companies: {', '.join(article['companies'])}"))
        pdf.ln(8)

    pdf.set_y(-15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()} — Generated by FidSync", 0, 0, 'C')

    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_path.name)
    return temp_path.name

def run():
    st.markdown("## Article Analyzer")
    depth = st.slider("Summary Depth (bullet points)", 3, 10, 5)
    url = st.text_input("Enter Article URL")

    if st.button("Analyze"):
        if not url.strip():
            st.warning("Please enter a valid article URL.")
            return

        with st.spinner("Processing article..."):
            title, text, date, authors = fetch_article(url)
            if text.startswith("[Error]"):
                st.error(text)
                return

            summary, points, facts, _ = summarize_article(text, depth)
            tickers, companies = detect_tickers_and_companies(text)
            sentiment = score_sentiment(summary)
            metrics = extract_metrics(text)
            source = get_domain(url)

            article_data = {
                "title": title or "Untitled",
                "date": date.strftime("%B %d, %Y") if date else "N/A",
                "summary": summary,
                "key_points": points,
                "metrics": metrics,
                "tickers": tickers,
                "companies": companies,
                "sentiment": sentiment,
                "source": source,
                "author": ', '.join(authors) if authors else "Unknown"
            }

            st.markdown(f"### {article_data['title']}")
            st.markdown(f"**Date:** {article_data['date']}  \n**Source:** {article_data['source']}")
            if article_data['author']:
                st.markdown(f"**Author:** {article_data['author']}")
            st.markdown(f"**Sentiment:** {article_data['sentiment']}")
            st.markdown(f"**Summary:** {article_data['summary']}")
            if article_data['key_points']:
                st.markdown("**Key Points:**")
                for pt in article_data['key_points']:
                    st.markdown(f"- {pt}")
            if article_data['metrics']:
                st.markdown("**Notable Metrics:**")
                for line in article_data['metrics']:
                    st.markdown(f"- {line}")
            if article_data['tickers'] or article_data['companies']:
                st.markdown("**Mentions:**")
                if article_data['tickers']:
                    links = [f"[{t}](https://www.google.com/finance/quote/{t}:NASDAQ)" for t in article_data['tickers']]
                    st.markdown(f"Tickers: {' | '.join(links)}")
                if article_data['companies']:
                    st.markdown(f"Companies: {', '.join(article_data['companies'])}")
            st.markdown("---")

            pdf_path = generate_pdf_digest([article_data])
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download PDF Summary", f, file_name="article_summary.pdf")

    st.info("Note: This is an automated tool for summarizing financial articles. Always double-check key information.")
""")

display_dataframe_to_user("Final Article Analyzer Script", [{"filename": "article_analyzer.py", "code": article_analyzer_script}])
