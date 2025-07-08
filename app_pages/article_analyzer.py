import streamlit as st
import pdfplumber
from docx import Document
import re
from collections import Counter

# -------------------------
# Article Text Extraction
# -------------------------

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            return "\n".join([page.extract_text() or "" for page in pdf.pages])
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    return None

# -------------------------
# Article Analysis
# -------------------------

def analyze_article(text, max_points=5):
    # Basic sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if len(s.strip()) > 40]

    # Word frequency for scoring
    words = re.findall(r'\w+', text.lower())
    stopwords = set([
        "the", "and", "a", "to", "of", "in", "that", "is", "on", "for", "with", "as",
        "this", "by", "an", "be", "are", "or", "it", "from", "at", "was", "but", "we",
        "not", "have", "has", "you", "they", "their", "can", "if", "will", "about"
    ])
    word_freq = Counter(w for w in words if w not in stopwords)

    # Score sentences
    sentence_scores = {}
    for sentence in sentences:
        score = sum(word_freq.get(word.lower(), 0) for word in re.findall(r'\w+', sentence))
        sentence_scores[sentence] = score

    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)

    # Main idea = top sentence
    main_idea = top_sentences[0] if top_sentences else "No clear main idea found."

    # Key points = next top sentences
    key_points = top_sentences[1:max_points + 1] if len(top_sentences) > 1 else []

    # Highlight facts or quotes (sentences with numbers or quotation marks)
    fact_lines = [s for s in sentences if re.search(r'\d|“|”|\"', s)]
    fact_lines = fact_lines[:3]  # limit to top 3 facts/quotes

    return main_idea, key_points, fact_lines

# -------------------------
# Streamlit App UI
# -------------------------

def run():
    st.markdown("## 📰 Article Analyzer")
    st.markdown("Upload a `.pdf`, `.docx`, or `.txt` article to extract the main idea, key insights, and facts.")

    uploaded_file = st.file_uploader("Upload Article", type=["pdf", "docx", "txt"])

    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)
        if not raw_text:
            st.error("Unable to extract text from file.")
            return

        with st.expander("📄 Preview Extracted Text"):
            st.code(raw_text[:1000])

        st.markdown("### 🧠 Article Summary")

        main_idea, key_points, fact_lines = analyze_article(raw_text)

        st.markdown(f"**Main Idea**: {main_idea}")

        if key_points:
            st.markdown("**Key Supporting Points:**")
            for i, point in enumerate(key_points, 1):
                st.markdown(f"- {point}")

        if fact_lines:
            st.markdown("**Notable Quotes / Stats:**")
            for fact in fact_lines:
                st.markdown(f"> {fact}")

        st.success("✅ Analysis complete.")

    else:
        st.info("Upload an article file above to begin.")
