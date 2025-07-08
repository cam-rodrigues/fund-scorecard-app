import streamlit as st
import re
from newspaper import Article
from collections import Counter
from dateutil import parser as date_parser
from fpdf import FPDF
from datetime import datetime
import tempfile

# ========== Encoding Fix ==========
def safe(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

# ========== Company + Ticker Detection ==========
COMMON_COMPANIES = [
    "Apple", "Microsoft", "Amazon", "Tesla", "Meta", "Alphabet", "Nvidia", "JPMorgan",
    "Goldman Sachs", "Bank of America", "Walmart", "Berkshire Hathaway", "Netflix",
    "ExxonMobil", "Chevron", "Pfizer", "Johnson & Johnson", "Visa", "Mastercard"
]

def detect_tickers_and_companies(text):
    tickers = re.findall(r'\$?[A-Z]{2,5}(?:\.[A-Z])?', text)
    tickers = list(set([t.strip("$") for t in tickers if 2 <= len(t.strip("$")) <= 6]))
    companies = [name for name in COMMON_COMPANIES if name.lower() in text.lower()]
    return sorted(set(tickers)), sorted(set(companies))

# ========== Text-Based Summarization ==========
def summarize_article(text, max_points=5):
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 60]
    all_sentences, quotes, numbers = [], [], []

    words = re.findall(r'\w+', text.lower())
    stopwords = set([
        "the", "and", "a", "to", "of", "in", "that", "is", "on", "for", "with", "as",
        "this", "by", "an", "be", "are", "or", "it", "from", "at", "was", "but", "we",
        "not", "have", "has", "you", "they", "their", "can", "if", "will", "about"
    ])
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
            if re.search(r'[“”"]', sent):
                quotes.append(sent)
            if re.search(r'\d', sent):
                numbers.append(sent)

    sorted_sents = sorted(all_sentences, key=lambda x: x[1], reverse=True)
    main = sorted_sents[0][0] if sorted_sents else "No clear summary found."
    bullets = [s for s, _ in sorted_sents[1:max_points + 1]]
    facts = list(dict.fromkeys(quotes + numbers))[:3]
    return main, bullets, facts, freq

# ========== Article Fetching ==========
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
        return title, text, pub_date
    except Exception as e:
        return None, f"[Error] {e}", None

# ========== PDF Generator ==========
def generate_pdf_digest(summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # === Header ===
    title_text = "Finance Article Digest" if len(summaries) > 1 else "Finance Article Summary"
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 12, safe(title_text), ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, safe(datetime.now().strftime("%B %d, %Y")), ln=True, align='C')
    pdf.ln(10)

    for i, article in enumerate(summaries, 1):
        # === Article Title ===
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        pdf.set_font("Arial", 'B', 14)
        pdf.multi_cell(0, 10, safe(f"{i}. {article['title']}"))
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, safe(f"Published: {article['date']}"), ln=True)
        pdf.ln(1)

        # === Summary ===
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Summary:", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 8, safe(article["summary"]))
        pdf.ln(1)

        # === Key Points ===
        if article["key_points"]:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Key Points:", ln=True)
            pdf.set_font("Arial", '', 12)
            for pt in article["key_points"]:
                pdf.multi_cell(0, 8, safe(f"- {pt}"))
            pdf.ln(1)

        # === Mentions ===
        if article["tickers"] or article["companies"]:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Mentions:", ln=True)
            pdf.set_font("Arial", '', 12)
            if article["tickers"]:
                pdf.multi_cell(0, 8, safe(f"Tickers: {', '.join(article['tickers'])}"))
            if article["companies"]:
                pdf.multi_cell(0, 8, safe(f"Companies: {', '.join(article['companies'])}"))
        pdf.ln(6)

    # === Save ===
    temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_path.name)
    return temp_path.name

# ========== Streamlit UI ==========
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
                title, text, date = fetch_article(url)
                if text.startswith("[Error]"):
                    st.error(text)
                    return

                summary, points, facts, freq = summarize_article(text, depth)
                tickers, companies = detect_tickers_and_companies(text)
                summaries.append({
                    "title": title or f"Article {i+1}",
                    "date": date.strftime("%B %d, %Y") if date else "N/A",
                    "summary": summary,
                    "key_points": points,
                    "tickers": tickers,
                    "companies": companies
                })

        for article in summaries:
            st.markdown(f"### {article['title']}")
            st.markdown(f"**Date:** {article['date']}")
            st.markdown(f"**Summary:** {article['summary']}")
            if article['key_points']:
                st.markdown("**Key Points:**")
                for pt in article['key_points']:
                    st.markdown(f"- {pt}")
            if article['tickers'] or article['companies']:
                st.markdown("**Mentions:**")
                if article['tickers']:
                    st.markdown(f"`Tickers:` {' '.join(article['tickers'])}")
                if article['companies']:
                    st.markdown(f"`Companies:` {', '.join(article['companies'])}")
            st.markdown("---")

        pdf_path = generate_pdf_digest(summaries)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF Summary", f, file_name="article_digest.pdf")

    st.info("Note: This summary is best-effort. Please verify all information before relying on results.")
