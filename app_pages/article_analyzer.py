import streamlit as st
import re
from collections import Counter
from newspaper import Article

st.set_page_config(page_title="Article Analyzer", layout="wide")

# -------------------------
# Fetch Article from URL
# -------------------------

def fetch_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.title, article.text
    except Exception as e:
        return None, f"Error fetching article: {e}"

# -------------------------
# Analyze Text
# -------------------------

def analyze_article(text, max_points=5):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s) > 40]

    words = re.findall(r'\w+', text.lower())
    stopwords = set([
        "the", "and", "a", "to", "of", "in", "that", "is", "on", "for", "with", "as",
        "this", "by", "an", "be", "are", "or", "it", "from", "at", "was", "but", "we",
        "not", "have", "has", "you", "they", "their", "can", "if", "will", "about"
    ])
    word_freq = Counter(w for w in words if w not in stopwords)

    sentence_scores = {
        sentence: sum(word_freq.get(w.lower(), 0) for w in re.findall(r'\w+', sentence))
        for sentence in sentences
    }

    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    main_idea = top_sentences[0] if top_sentences else "No clear main idea found."
    key_points = top_sentences[1:max_points + 1]
    fact_lines = [s for s in sentences if re.search(r'\d|“|”|\"', s)][:3]

    return main_idea, key_points, fact_lines

# -------------------------
# UI
# -------------------------

def run():
    st.markdown("""
        <style>
            .big-header { font-size: 2rem; font-weight: 800; margin-bottom: 0.3rem; color: #1c2e4a; }
            .section-title { font-size: 1.25rem; font-weight: 700; margin-top: 1.5rem; color: #2b3e55; }
            .quote-box {
                background-color: #f8f9fb;
                padding: 0.75rem;
                border-left: 4px solid #a0b4d6;
                border-radius: 6px;
                margin-bottom: 0.75rem;
                font-size: 0.96rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="big-header">Article Analyzer</div>', unsafe_allow_html=True)
    st.markdown("Paste a link to a news article or blog post. The tool will extract and summarize key insights.")

    with st.container():
        url = st.text_input("Article URL")

        if url and st.button("Analyze"):
            with st.spinner("Fetching and analyzing..."):
                title, content = fetch_article_text(url)

            if not content or content.startswith("Error"):
                st.error(content)
                return

            st.success(f"Analyzed: {title}")

            with st.expander("View Full Text", expanded=False):
                st.code(content[:1500])

            main_idea, key_points, fact_lines = analyze_article(content)

            st.markdown('<div class="section-title">Main Idea</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quote-box">{main_idea}</div>', unsafe_allow_html=True)

            if key_points:
                st.markdown('<div class="section-title">Key Points</div>', unsafe_allow_html=True)
                for pt in key_points:
                    st.markdown(f"- {pt}")

            if fact_lines:
                st.markdown('<div class="section-title">Notable Quotes / Stats</div>', unsafe_allow_html=True)
                for fact in fact_lines:
                    st.markdown(f'<div class="quote-box">{fact}</div>', unsafe_allow_html=True)

            full_summary = f"""Title: {title}\n\nMain Idea:\n{main_idea}\n\nKey Points:\n"""
            full_summary += "\n".join(f"- {pt}" for pt in key_points)
            full_summary += "\n\nQuotes/Stats:\n" + "\n".join(f"> {fact}" for fact in fact_lines)

            st.download_button("Download Summary (.txt)", data=full_summary, file_name="article_summary.txt")

        elif not url:
            st.info("Paste an article link above and click 'Analyze' to begin.")
