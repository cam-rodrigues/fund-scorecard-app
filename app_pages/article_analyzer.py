# app_pages/article_analyzer.py

import streamlit as st
import re
from collections import Counter
from newspaper import Article
from fpdf import FPDF
from io import BytesIO

# -------------------------
# PDF Generator
# -------------------------

def generate_pdf(title, main, bullets, facts):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Article Summary", ln=1)

    if title:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Title:", ln=1)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, title + "\n")

    if main:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Main Idea:", ln=1)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, main + "\n")

    if bullets:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Key Points:", ln=1)
        pdf.set_font("Arial", "", 11)
        for pt in bullets:
            pt = pt.replace("•", "-")
            pdf.multi_cell(0, 8, f"- {pt}")

    if facts:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Notable Facts or Quotes:", ln=1)
        pdf.set_font("Arial", "I", 11)
        for f in facts:
            safe_fact = f.replace("“", '"').replace("”", '"').replace("•", "-")
            pdf.multi_cell(0, 8, f'"{safe_fact}"')

    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer

# -------------------------
# Core Summarizer
# -------------------------

def upgraded_analyze_article(text, max_points=5):
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

    return main, bullets, facts

# -------------------------
# Fetch Article
# -------------------------

def fetch_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.title, article.text
    except Exception as e:
        return None, f"Unable to extract article: {e}"

# -------------------------
# Streamlit UI
# -------------------------

def run():
    st.markdown("""
        <style>
            .page-title { font-size: 1.75rem; font-weight: 700; color: #1c2e4a; margin-bottom: 1rem; }
            .section-label { font-size: 1.1rem; font-weight: 600; margin-top: 2rem; color: #2b3e55; }
            .box {
                background-color: #f4f6fa;
                padding: 0.75rem;
                border-left: 4px solid #8ba8c5;
                border-radius: 6px;
                margin-bottom: 1rem;
                font-size: 0.95rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-title">Article Analyzer</div>', unsafe_allow_html=True)

    st.text_input("Article URL", key="url_input", help="Paste a link to a news article or blog post.")
    st.slider("Number of key points", 3, 10, value=5, key="bullet_count")

    if st.button("Analyze Article"):
        url = st.session_state["url_input"]
        max_points = st.session_state["bullet_count"]

        if not url:
            st.warning("Please paste an article URL.")
            return

        with st.spinner("Processing..."):
            title, content = fetch_article_text(url)

        if not content or content.startswith("Unable"):
            st.error(content)
            return

        st.markdown(f'<div class="section-label">Title</div>', unsafe_allow_html=True)
        if title and len(title.split()) > 2:
            st.markdown(f'<div class="box">{title}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="box">[Title not reliably detected]</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="section-label">Summary</div>', unsafe_allow_html=True)
        main, bullets, facts = upgraded_analyze_article(content, max_points)
        st.markdown(f'<div class="box">{main}</div>', unsafe_allow_html=True)

        if bullets:
            st.markdown(f'<div class="section-label">Key Points</div>', unsafe_allow_html=True)
            for pt in bullets:
                st.markdown(f"- {pt}")

        if facts:
            st.markdown(f'<div class="section-label">Notable Facts or Quotes</div>', unsafe_allow_html=True)
            for f in facts:
                st.markdown(f'<div class="box">{f}</div>', unsafe_allow_html=True)

        # PDF Export
        pdf_bytes = generate_pdf(title, main, bullets, facts)
        st.download_button("📄 Download PDF", data=pdf_bytes, file_name="article_summary.pdf", mime="application/pdf")

    st.markdown("---")
    st.caption("This tool extracts and summarizes publicly available articles from news sites and blogs.")

    st.markdown("""
    <div style="margin-top: 2rem; font-size: 0.85rem; color: #555;">
    ⚠️ <strong>Note:</strong> This tool uses automated methods to extract and summarize article content. Please double-check all information before relying on it for professional or personal use.
    </div>
    """, unsafe_allow_html=True)
