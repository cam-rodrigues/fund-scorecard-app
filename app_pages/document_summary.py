import spacy
from heapq import nlargest

# Load English model
nlp = spacy.load("en_core_web_sm")

def summarize_text(text, max_sentences=5):
    doc = nlp(text)

    sentence_scores = {}
    for sent in doc.sents:
        score = 0
        for token in sent:
            if token.ent_type_ or token.pos_ in ["NOUN", "VERB", "PROPN"]:
                score += 1
        if len(sent.text.strip()) > 20:
            sentence_scores[sent.text] = score

    summary = nlargest(max_sentences, sentence_scores, key=sentence_scores.get)
    return " ".join(summary)
