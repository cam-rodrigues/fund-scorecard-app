import streamlit as st
import pdfplumber
from docx import Document
import os

def summarize_text(text, max_sentences=5):
    import heapq
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from string import punctuation

    nltk.download("punkt")
    nltk.download("stopwords")

    sentences = sent_tokenize(text)
    if len(sentences) <= max_sentences:
        return text

    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english") + list(punctuation))

    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    sentence_scores = {}
    for sent in sentences:
        for word in word_tokenize(sent.lower()):
            if word in word_freq:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_freq[word]

    summary_sentences = heapq.nlargest(max_sentences, sentence_scores, key=sentence_scores.get)
    return " ".join(summary_sentences)

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
    st.markdown("Upload a `.pdf`, `.docx`, or `.txt` file to get a smart summary.")
    uploaded_file = st.file_uploader("Choose a document file", type=["pdf", "docx", "txt"])

    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)
        if raw_text:
            with st.spinner("Summarizing..."):
                summary = summarize_text(raw_text)
            st.success("Summary generated:")
            st.markdown(f"**File Name:** {uploaded_file.name}")
            st.markdown("### 📄 Summary")
            st.write(summary)
        else:
            st.error("Unsupported file or failed to extract text.")
