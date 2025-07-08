import streamlit as st
import pdfplumber
from docx import Document
import re
from collections import Counter

def summarize_text(text, max_sentences=5):
    # Clean and split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]  # remove tiny fragments

    if len(sentences) <= max_sentences:
        return "\n".join(sentences)

    # Word frequency scoring
    words = re.findall(r'\w+', text.lower())
    stopwords = set([
        "the", "and", "a", "to", "of", "in", "that", "is", "on", "for", "with", "as",
        "this", "by", "an", "be", "are", "or", "it", "from", "at", "was", "but", "we",
        "not", "have", "has", "you", "they", "their", "can", "if", "will", "about"
    ])
    common = Counter(w for w in words if w not in stopwords)

    sentence_scores = {}
    for sentence in sentences:
        sentence_words = re.findall(r'\w+', sentence.lower())
        score = sum(common.get(word, 0) for word in sentence_words)
        sentence_scores[sentence] = score

    # Sort and return best-scoring sentences
    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    return "\n".join(top_sentences)

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            return "\n".join([page.extract_text() or "" for page in pdf.pages])
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        return None

def run():
    st.markdown("## Document Summary Tool")
    st.markdown("Upload a `.pdf`, `.docx`, or `.txt` file to generate a smart summary.")

    uploaded_file = st.file_uploader("Choose a document file", type=["pdf", "docx", "txt"])

    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)
        if raw_text:
            st.markdown("### Raw Text Preview")
            st.code(raw_text[:1000])  # First 1000 chars

            # Show sentence count for debugging
            sentences_preview = re.split(r'(?<=[.!?])\s+', raw_text.strip())
            st.markdown("### Sentence Count")
            st.write(f"{len(sentences_preview)} sentences found")

            with st.spinner("Summarizing..."):
                summary = summarize_text(raw_text)

            st.success("Summary generated:")
            st.markdown(f"**File Name:** {uploaded_file.name}")
            st.markdown("### 📄 Summary")
            st.write(summary)
        else:
            st.error("Unsupported file or failed to extract text.")
