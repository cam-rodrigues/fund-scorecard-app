import streamlit as st
import re
from collections import Counter
from newspaper import Article

st.set_page_config(page_title="Article Analyzer", layout="wide")

# -------------------------
# Core logic (no AI)
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
    main = sorted_sents[0][0] if sorted_sents else "We couldn’t find a clear summary."
    bullets = [s for s, _ in sorted_sents[1:max_points + 1]]
    facts = list(dict.fromkeys(quotes + numbers))[:3]

    return main, bullets, facts

def fetch_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.title, article.text
    except Exception as e:
        return None, f"Oops! Couldn’t read the article: {e}"

# -------------------------
# Simple UI for Beginners
# -------------------------

def run():
    st.markdown("""
        <style>
            .title { font-size: 2rem; font-weight: bold; color: #203040; margin-bottom: 1rem; }
            .step { font-weight: bold; margin-top: 1.5rem; font-size: 1.1rem; }
            .box {
                background-color: #f8f9fb;
                padding: 0.75rem;
                border-left: 4px solid #6b90c6;
                border-radius: 6px;
                margin-bottom: 1rem;
                font-size: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">Quick Article Analyzer</div>', unsafe_allow_html=True)
    st.markdown("This tool helps you get the main idea and key points from any article. Just follow the steps:")

    st.markdown('<div class="step">Step 1: Paste the link to the article</div>', unsafe_allow_html=True)
    url = st.text_input("Paste URL here")

    st.markdown('<div class="step">Step 2: Choose how many points you want</div>', unsafe_allow_html=True)
    max_points = st.slider("Number of bullet points", 3, 10, value=5)

    if url and st.button("Get Summary"):
        with st.spinner("Reading the article..."):
            title, content = fetch_article_text(url)

        if not content or content.startswith("Oops"):
            st.error(content)
            return

        st.success("Done! Here's what we found:")
        main, bullets, facts = upgraded_analyze_article(content, max_points)

        st.markdown(f"<div class='step'>Title:</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='box'>{title}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='step'>What's the article mostly about?</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='box'>{main}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='step'>Important points:</div>", unsafe_allow_html=True)
        for b in bullets:
            st.markdown(f"- {b}")

        if facts:
            st.markdown(f"<div class='step'>Interesting facts or quotes:</div>", unsafe_allow_html=True)
            for f in facts:
                st.markdown(f"<div class='box'>{f}</div>", unsafe_allow_html=True)

        summary_txt = f"""Title: {title}\n\nSummary:\n{main}\n\nKey Points:\n"""
        summary_txt += "\n".join(f"- {b}" for b in bullets)
        summary_txt += "\n\nFacts:\n" + "\n".join(f"> {f}" for f in facts)

        st.download_button("Download as .txt", data=summary_txt, file_name="summary.txt")

    elif not url:
        st.info("Paste an article link above and click the button.")
