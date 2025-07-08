import streamlit as st
import pdfplumber
from docx import Document
import re

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

# -------------------------
# Simple Heading-Based Summary
# -------------------------

def extract_headings_summary(text, lines_per_section=3):
    lines = text.splitlines()
    summary = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Heuristic: heading is ALL CAPS or Title Case or ends with ":"
        if (line.isupper() and len(line) > 5) or re.match(r'^([A-Z][a-z]+ ){1,5}[A-Z][a-z]+$', line) or line.endswith(":"):
            section = [f"### {line}"]
            # Capture next few lines under the heading
            for j in range(1, lines_per_section + 1):
                if i + j < len(lines):
                    content_line = lines[i + j].strip()
                    if content_line:
                        section.append(f"- {content_line}")
            summary.append("\n".join(section))
            i += lines_per_section
        i += 1
    return "\n\n".join(summary)


# --------------------------
# Streamlit UI + Interaction
# --------------------------

def run():
    st.markdown("## 📄 Document Summary Tool")
    st.markdown("Upload a `.pdf`, `.docx`, or `.txt` file to extract a structured summary based on headings.")

    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])

    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)

        if not raw_text:
            st.error("Failed to extract text from file.")
            return

        # Optional preview
        with st.expander("🔍 Preview Extracted Text"):
            st.code(raw_text[:1000])

        st.markdown("### 🧠 Structured Summary")
        summary = extract_headings_summary(raw_text)
        if summary.strip():
            st.markdown(summary)
        else:
            st.warning("No clear headings found. The document may need manual review.")
