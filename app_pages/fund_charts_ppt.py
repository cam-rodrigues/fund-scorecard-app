import streamlit as st
import pdfplumber
from together import Together

def run():
    st.set_page_config(page_title="AI-Powered Fund Summary", layout="wide")
    st.title("🧠 AI-Powered Fund Summary")
    st.markdown("Upload an MPI PDF to generate a smart summary of the financial insights.")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="ai_summary_upload")

    if not uploaded_file:
        st.stop()

    # Extract full PDF text
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    if not full_text.strip():
        st.error("No text could be extracted from this PDF.")
        st.stop()

    # Prepare prompt and model
    api_key = st.secrets["together"]["api_key"]
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    prompt = f"""Summarize this investment report like you're preparing key insights for a financial advisor. 
Focus on fund performance, risk metrics, notable portfolio positions, and management commentary.

{full_text[:16000]}"""

    # Send to Together AI
    with st.spinner("Generating summary using Together AI..."):
        try:
            client = Together(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            st.subheader("📊 Fund Summary")
            st.markdown(response.choices[0].message.content.strip())
        except Exception as e:
            st.error(f"❌ Together AI Error: {e}")
