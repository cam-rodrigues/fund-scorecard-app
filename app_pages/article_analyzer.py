import spacy
from spacy.cli import download as spacy_download

# Check and load model (only runs once)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    spacy_download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

import os
os.system("python -m spacy download en_core_web_sm")
os.system("python -m textblob.download_corpora")

import streamlit as st
import re
from newspaper import Article
from collections import Counter
from dateutil import parser as date_parser
from fpdf import FPDF
from datetime import datetime
import tempfile
import socket
import urllib.parse
import spacy
from textblob import TextBlob

nlp = spacy.load("en_core_web_sm")

# === Helpers ===
def safe(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def get_domain(url):
    try:
        return urllib.parse.urlparse(url).netloc.replace("www.", "")
    except:
        return "Unknown source"

def score_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    return "Neutral"

def detect_tickers_and_companies(text):
    tickers = re.findall(r'\$?[A-Z]{2,5}(?:\.[A-Z])?', text)
    tickers = list(set([t.strip("$") for t in tickers if 2 <= len(t.strip("$")) <= 6]))
    doc = nlp(text)
    companies = sorted(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
    return sorted(set(tickers)), companies

def extract_metrics(text):
    lines = text.split('\n')
    metrics = []
    for line in lines:
        if any(keyword in line.lower() for keyword in ["eps", "revenue", "growth", "net income", "guidance", "margin"]):
            if re.search(r'\d', line):
                metrics.append(line.strip())
    return metrics[:5]

# === Article Summarizer ===
def summarize_article(text, max_points=5):
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 60]
    all_sentences, quotes, numbers = [], [], []

    words = re.findall(r'\w+', text.lower())
    stopwords = set(["the", "and", "a", "to", "of", "in", "that", "is", "on", "for", "with", "as", "this", "by", "an", "be", "are", "or", "it", "from", "at", "was", "but", "we", "not", "have", "has", "you", "they", "their", "can", "if", "will", "about"])
    freq = Counter(w for w in words if w not in stopwords)
    signal_phrases = ["according to", "in conclusion", "experts say", "overall", "key finding"]

    for i, para in enumerate(paragraphs):
        sentences = re.split(r'(?<=[.!?])\s+', para)
        para_boost = 1.5 if i == 0 or i == len(paragraphs) - 1 else 1.0
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 40:
                continue
            base = sum(freq.get(w.lower(), 0) for w in re.findall(r'\w+', sent))
            bonus = 3 if any(p in sent.lower() for p in signal_phrases) else 0
            score = base * para_boost + bonus
            all_sentences.append((sent, score))
            if re.search(r'[“”"]', sent): quotes.append(sent)
            if re.search(r'\d', sent): numbers.append(sent)

    sorted_sents = sorted(all_sentences, key=lambda x: x[1], reverse=True)
    main = sorted_sents[0][0] if sorted_sents else "No clear summary found."
    bullets = [s for s, _ in sorted_sents[1:max_points + 1]]
    facts = list(dict.fromkeys(quotes + numbers))[:3]
    return main, bullets, facts, freq

# === Article Downloader ===
def fetch_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        title = article.title
        text = article.text
        pub_date = article.publish_date
        if not pub_date:
            match = re.search(r'(Published|Updated)[:\s]+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
            if match:
                pub_date = date_parser.parse(match.group(2))
        return title, text, pub_date, article.authors
    except Exception as e:
        return None, f"[Error] {e}", None, []

# === PDF Export ===
def generate_pdf_digest(summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()

    title_text = "Finance Article Digest" if len(summaries) > 1 else "Finance Article Summary"
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 12, safe(title_text), ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, safe(datetime.now().strftime("%B %d, %Y")), ln=True, align='C')
    pdf.ln(8)

    for i, article in enumerate(summaries, 1):
        pdf.set_draw_color(190, 190, 190)
        pdf.set_line_width(0.4)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 14)
        pdf.multi_cell(0, 10, safe(f"{i}. {article['title']}"))
        pdf.set_font("Arial", 'I', 11)
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

    is_digest = st.toggle("Daily Digest Mode", value=False)
    depth = st.slider("Summary Depth (bullet points)", 3, 10, 5)

    urls = []
    if is_digest:
        urls.append(st.text_input("Article URL 1", key="url1"))
        urls.append(st.text_input("Article URL 2", key="url2"))
    else:
        urls.append(st.text_input("Article URL", key="url"))

    if st.button("Analyze"):
        summaries = []

        for i, url in enumerate(urls):
            if not url.strip():
                st.warning(f"Missing URL for Article {i+1}")
                return

            with st.spinner(f"Processing Article {i+1}..."):
                title, text, date, authors = fetch_article(url)
                if text.startswith("[Error]"):
                    st.error(text)
                    return

                summary, points, facts, _ = summarize_article(text, depth)
                tickers, companies = detect_tickers_and_companies(text)
                sentiment = score_sentiment(summary)
                metrics = extract_metrics(text)
                source = get_domain(url)

                summaries.append({
                    "title": title or f"Article {i+1}",
                    "date": date.strftime("%B %d, %Y") if date else "N/A",
                    "summary": summary,
                    "key_points": points,
                    "metrics": metrics,
                    "tickers": tickers,
                    "companies": companies,
                    "sentiment": sentiment,
                    "source": source,
                    "author": ', '.join(authors) if authors else "Unknown"
                })

        for article in summaries:
            st.markdown(f"### {article['title']}")
            st.markdown(f"**Date:** {article['date']}  \n**Source:** {article['source']}")
            if article['author']:
                st.markdown(f"**Author:** {article['author']}")
            st.markdown(f"**Sentiment:** {article['sentiment']}")
            st.markdown(f"**Summary:** {article['summary']}")
            if article['key_points']:
                st.markdown("**Key Points:**")
                for pt in article['key_points']:
                    st.markdown(f"- {pt}")
            if article['metrics']:
                st.markdown("**Notable Metrics:**")
                for line in article['metrics']:
                    st.markdown(f"- {line}")
            if article['tickers'] or article['companies']:
                st.markdown("**Mentions:**")
                if article['tickers']:
                    links = [f"[{t}](https://www.google.com/finance/quote/{t}:NASDAQ)" for t in article['tickers']]
                    st.markdown(f"Tickers: {' | '.join(links)}")
                if article['companies']:
                    st.markdown(f"Companies: {', '.join(article['companies'])}")
            st.markdown("---")

        pdf_path = generate_pdf_digest(summaries)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF Summary", f, file_name="article_digest.pdf")

    st.info("Note: This is an automated tool for quick financial article digestion. Always verify summaries before use.")
