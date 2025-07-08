import streamlit as st
import pdfplumber
from docx import Document
import re
from collections import Counter

# ------------------------
# Text Summarization Logic
# ------------------------

def summarize_text(text, max_sentences=5):
    # Break into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) <= max_sentences:
        return "\n".join(sentences)

    # Score words
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
        sentence_words = re.findall(r'\w+', sentence.lower())
        score = sum(word_freq.get(word, 0) for word in sentence_words)
        sentence_scores[sentence] = score

    # Select top-scoring sentences
    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    return "\n".join(top_sentences)


# -------------------------
# File Extraction Logic
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


# --------------------------
# Streamlit UI + Interaction
# --------------------------

def run():
    st.markdown("## 📄 Document Summary Tool")
    st.markdown("Upload a `.pdf`, `.docx`, or `.txt` file to generate a clean summary.")

    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])

    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)

        if not raw_text:
            st.error("Failed to extract text from file.")
            return

        # Optional debug/preview
        with st.expander("🔍 Preview Extracted Text"):
            st.code(raw_text[:1000])

        sentence_count = len(re.split(r'(?<=[.!?])\s+', raw_text.strip()))
        st.info(f"Found {sentence_count} sentences in the document.")

        # Generate and display summary
        with st.spinner("Generating summary..."):
            summary = summarize_text(raw_text)

        st.success("✅ Summary Complete")
        st.markdown(f"**File:** `{uploaded_file.name}`")
        st.markdown("### ✨ Summary")
        st.write(summary)
