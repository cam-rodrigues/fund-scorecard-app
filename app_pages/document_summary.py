import spacy
from heapq import nlargest

# --- Load model with fallback ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- Local summarizer based on noun/verb/entity scoring ---
def summarize_text(text, max_sentences=5):
    doc = nlp(text)
    sentence_scores = {}

    for sent in doc.sents:
        score = sum(1 for token in sent if token.ent_type_ or token.pos_ in ["NOUN", "VERB", "PROPN"])
        if len(sent.text.strip()) > 20:
            sentence_scores[sent.text] = score

    summary = nlargest(max_sentences, sentence_scores, key=sentence_scores.get)
    return " ".join(summary)
