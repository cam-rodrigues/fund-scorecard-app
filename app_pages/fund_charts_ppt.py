import streamlit as st
import pdfplumber
import requests
import re
import os

def call_ai_summary(api_type, text):
    if api_type == "Together AI":
        url = "https://api.together.xyz/v1/chat/completions"
        headers = {"Authorization": f"Bearer {os.environ['api_key']}"}
        body = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": [
                {"role": "system", "content": "You're a finance analyst. Summarize insights from this investment fund report."},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
        }
        r = requests.post(url, json=body, headers=headers)
        return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")

    elif api_type == "OpenAI":
        import openai
        openai.api_key = os.environ["OPENAI_API_KEY"]
        chat = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a financial analyst. Summarize this PDF section for an advisor."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
        )
        return chat.choices[0].message.content

    else:
        return "❌ Unknown API selected."

def extract_pdf_chunks(pdf_file, max_chars=3000):
    with pdfplumber.open(pdf_file) as pdf:
        full_text = " ".join(page.extract_text() or "" for page in pdf.pages)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    return [full_text[i:i+max_chars] for i in range(0, len(full_text), max_chars)]

def run():
    st.title("🧠 AI-Powered Fund Summary")
    st.markdown("Upload an MPI PDF and choose an AI model to generate a smart summary of the financial insights.")

    api_type = st.selectbox("Choose Model", ["Together AI", "OpenAI"])
    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="ai_fund_pdf")

    if pdf_file and api_type:
        with st.spinner("Extracting and summarizing..."):
            chunks = extract_pdf_chunks(pdf_file)
            summaries = []

            for i, chunk in enumerate(chunks):
                try:
                    summary = call_ai_summary(api_type, chunk)
                    summaries.append(f"### Section {i+1}\n{summary.strip()}")
                except Exception as e:
                    summaries.append(f"**Error in section {i+1}:** {str(e)}")

        st.markdown("## 📊 Summary")
        for s in summaries:
            st.markdown(s)

