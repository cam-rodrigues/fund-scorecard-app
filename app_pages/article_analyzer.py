import streamlit as st
import re
from collections import Counter
from newspaper import Article

# -------------------------
# Article Extraction from URL
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
# Article Analysis
# -------------------------

def analyze_article(text, max_points=5):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if len(s.strip()) > 40]

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
# Streamlit UI
# -------------------------

def run():
    st.markdown("## 🌐 Article Analyzer (via URL)")
    st.markdown("Paste a link to a news article, blog post, or report.")

    url = st.text_input("Enter Article URL")
    if url and st.button("Analyze Article"):
        with st.spinner("Fetching and processing..."):
            title, content = fetch_article_text(url)

        if not content or content.startswith("Error"):
            st.error(content)
            return

        st.success(f"✅ Fetched: {title}")
        with st.expander("📄 Full Text Preview"):
            st.code(content[:1000])

        main_idea, key_points, fact_lines = analyze_article(content)

        st.markdown("### 🧠 Main Idea")
        st.markdown(f"> **{main_idea}**")

        st.markdown("### 🔍 Key Points")
        for point in key_points:
            st.markdown(f"- {point}")

        st.markdown("### 📊 Notable Quotes or Stats")
        for fact in fact_lines:
            st.markdown(f"> {fact}")

        full_summary = f"""Title: {title}\n\nMain Idea:\n{main_idea}\n\nKey Points:\n"""
        full_summary += "\n".join(f"- {pt}" for pt in key_points)
        full_summary += "\n\nQuotes/Stats:\n" + "\n".join(f"> {fact}" for fact in fact_lines)

        st.download_button("📥 Download Summary (.txt)", data=full_summary, file_name="article_summary.txt")
