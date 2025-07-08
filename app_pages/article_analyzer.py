import streamlit as st
import re
from collections import Counter
from newspaper import Article

st.set_page_config(page_title="Article Analyzer", layout="wide")

# -------------------------
# Summarizer (No AI)
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

    return main, bullets, facts, freq

# -------------------------
# Fetch Article
# -------------------------

def fetch_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.title, article.text, article.publish_date
    except Exception as e:
        return None, f"Unable to extract article: {e}", None

# -------------------------
# Financial Term Extraction
# -------------------------

def extract_financial_terms(freq, top_n=5):
    finance_terms = [
        "inflation", "deficit", "revenue", "equity", "bond", "fund", "interest", "rate",
        "growth", "market", "fiscal", "capital", "yield", "investment", "earnings",
        "valuation", "credit", "portfolio", "liquidity", "debt"
    ]
    filtered = {k: v for k, v in freq.items() if k in finance_terms}
    return sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]

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

    st.text_input("Article URL", key="url_input", help="Paste a link to a finance-related news article or blog post.")
    st.slider("Number of key points", 3, 10, value=5, key="bullet_count")

    if st.button("Analyze Article"):
        url = st.session_state["url_input"]
        max_points = st.session_state["bullet_count"]

        if not url:
            st.warning("Please paste an article URL.")
            return

        with st.spinner("Processing..."):
            title, content, pub_date = fetch_article_text(url)

        if not content or content.startswith("Unable"):
            st.error(content)
            return

        st.markdown(f'<div class="section-label">Title</div>', unsafe_allow_html=True)
        if title and len(title.split()) > 2:
            st.markdown(f'<div class="box">{title}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="box">[Title not reliably detected]</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="section-label">Publication Date</div>', unsafe_allow_html=True)
        if pub_date:
            st.markdown(f'<div class="box">{pub_date.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="box">[Not available]</div>', unsafe_allow_html=True)


        main, bullets, facts, freq = upgraded_analyze_article(content, max_points)

        st.markdown(f'<div class="section-label">Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="box">{main}</div>', unsafe_allow_html=True)

        if bullets:
            st.markdown(f'<div class="section-label">Key Points</div>', unsafe_allow_html=True)
            for pt in bullets:
                st.markdown(f"- {pt}")

        if facts:
            st.markdown(f'<div class="section-label">Notable Facts or Quotes</div>', unsafe_allow_html=True)
            for f in facts:
                st.markdown(f'<div class="box">{f}</div>', unsafe_allow_html=True)

        top_terms = extract_financial_terms(freq)
        if top_terms:
            st.markdown(f'<div class="section-label">Frequent Financial Terms</div>', unsafe_allow_html=True)
            st.markdown(" ".join(f"`{term}`" for term, _ in top_terms))

        text_output = f"""Title: {title}\n\nSummary:\n{main}\n\nKey Points:\n"""
        text_output += "\n".join(f"- {pt}" for pt in bullets)
        text_output += "\n\nFacts or Quotes:\n" + "\n".join(f"> {f}" for f in facts)
        text_output += "\n\nFrequent Financial Terms:\n" + ", ".join(term for term, _ in top_terms)

        st.download_button("Download Summary", data=text_output, file_name="summary.txt")

    st.markdown("---")
    st.caption("This tool extracts and summarizes publicly available finance articles from news sites and blogs.")

    st.markdown("""
    <div style="margin-top: 2rem; font-size: 0.85rem; color: #555;">
    ⚠️ <strong>Note:</strong> This tool uses automated methods to extract and summarize article content. Please double-check all information before relying on it for professional or personal use. Titles, facts, and dates may not always be perfectly accurate depending on the source.
    </div>
    """, unsafe_allow_html=True)
