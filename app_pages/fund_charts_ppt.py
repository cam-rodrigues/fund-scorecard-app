import streamlit as st
import pdfplumber
from together import Together
import textwrap

# === Config ===
MAX_CHARS = 15000  # Adjust based on model context limit (Together AI Mixtral supports ~32k tokens)

def run():
    st.set_page_config(page_title="AI-Powered Fund Summary", layout="wide")
    st.title("🧠 AI-Powered Fund Summary")
    st.markdown("Upload an MPI PDF to generate smart summaries of fund performance, risk, and financial insights.")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if not uploaded_file:
        st.stop()

    # Load PDF text
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n\n".join([page.extract_text() or "" for page in pdf.pages])

    # Split into chunks if too long
    chunks = textwrap.wrap(full_text, MAX_CHARS)

    # API setup
    api_key = st.secrets["together"]["api_key"]
    client = Together(api_key=api_key)
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    st.subheader("📊 Smart Summary")
    for i, chunk in enumerate(chunks):
        with st.spinner(f"Summarizing section {i+1} of {len(chunks)}..."):
            prompt = f"""
You're an investment analyst. Read the following section of an MPI fund report and summarize key insights for a financial advisor. 
Focus on fund names, performance metrics, risk ratios, expense ratios, and anything notable. Use bullet points.

Section {i+1}:
{chunk}
"""
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                )
                summary = response.choices[0].message.content.strip()
                st.markdown(f"**Section {i+1}:**")
                st.markdown(summary)
                st.divider()
            except Exception as e:
                st.error(f"❌ Error: {e}")
                break
