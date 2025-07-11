import streamlit as st
import pdfplumber
import os
from together import Together
from PyPDF2 import PdfReader

def run():
    st.set_page_config(page_title="AI-Powered Fund Summary", layout="wide")
    st.title("Fund Summary")
    st.markdown("Upload an MPI PDF  to generate a smart summary of the financial insights.")

    # === Select Model ===
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file is None:
        st.stop()

    # === Load PDF Text ===
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    # === Get API Key ===
    if model_choice == "Together AI":
        api_key = st.secrets["together"]["api_key"]
        model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
        prompt = f"""Summarize this investment report like you're preparing key insights for a financial advisor. Focus on fund performance, risk metrics, and anything notable.

{full_text[:16000]}"""

        with st.spinner("Generating summary with Together AI..."):
            try:
                client = Together(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                st.subheader("📊 Summary")
                st.markdown(response.choices[0].message.content.strip())
            except Exception as e:
                st.error(f"[Together AI Error] {e}")

    elif model_choice == "FinGPT (Hugging Face)":
        from huggingface_hub import InferenceClient
        api_key = st.secrets["huggingface"]["api_key"]
        model = "mrm8488/fingpt-financial-sentiment"

        with st.spinner("Generating summary with FinGPT..."):
            try:
                client = InferenceClient(model=model, token=api_key)
                response = client.text_generation(prompt=full_text[:2048])
                st.subheader("📊 Summary")
                st.markdown(response.strip())
            except Exception as e:
                st.error(f"[FinGPT Error] {e}")
