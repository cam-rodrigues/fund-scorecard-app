import streamlit as st
import docx2txt
import pdfplumber

def summarize_text(text, max_sentences=5):
    import re
    from heapq import nlargest
    from collections import defaultdict

    # Basic cleanup
    text = re.sub(r'\s+', ' ', text)
    sentences = re.split(r'(?<=[.!?]) +', text)

    # Simple scoring: count word frequency
    word_freq = defaultdict(int)
    for word in re.findall(r'\w+', text.lower()):
        word_freq[word] += 1

    # Score sentences based on word frequency
    sent_scores = {}
    for sent in sentences:
        for word in re.findall(r'\w+', sent.lower()):
            if word in word_freq:
                sent_scores[sent] = sent_scores.get(sent, 0) + word_freq[word]

    summary = ' '.join(nlargest(max_sentences, sent_scores, key=sent_scores.get))
    return summary

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif uploaded_file.name.endswith((".docx", ".doc")):
        return docx2txt.process(uploaded_file)
    else:
        return None

def run():
    st.markdown("## Document Summary Tool")
    st.markdown("Upload a PDF or Word document and get a quick summary.")

    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "doc"])

    if uploaded_file:
        with st.spinner("Extracting and summarizing text..."):
            text = extract_text_from_file(uploaded_file)
            if not text:
                st.error("Could not extract text from this file.")
                return

            summary = summarize_text(text)
            st.subheader("Summary")
            st.write(summary)

            with st.expander("Full Extracted Text"):
                st.text_area("Extracted Text", text, height=300)
