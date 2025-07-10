import streamlit as st
import pdfplumber
import requests
from collections import defaultdict

# === Load secrets ===
HUGGINGFACE_API_KEY = st.secrets.get("huggingface", {}).get("api_key", "")
TOGETHER_API_KEY = st.secrets.get("together", {}).get("api_key", "")

# === Config ===
FINGPT_ENDPOINT = "https://api-inference.huggingface.co/models/AI4Finance/FinGPT-4B-Chat"
TOGETHER_ENDPOINT = "https://api.together.xyz/v1/chat/completions"


def main():
    st.title("🔍 PDF Financial Term & Fund Navigator")
    st.markdown("Upload an MPI-style PDF. This tool extracts financial terms and fund sections, then lets you navigate to them.")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="fund_term_pdf")
    model_choice = st.selectbox("Choose Model", ["FinGPT (Hugging Face)", "Together AI"], key="model_picker")

    if uploaded_pdf:
        with pdfplumber.open(uploaded_pdf) as pdf:
            pages = [page.extract_text() for page in pdf.pages]

        with st.spinner("Analyzing PDF..."):
            found_terms = defaultdict(list)

            for i, text in enumerate(pages):
                if not text or len(text.strip()) < 100:
                    continue

                prompt = f"""You are a financial analyst. Read the following PDF page text and extract:
- Key financial metrics mentioned (e.g., Sharpe Ratio, Expense Ratio)
- Any fund name headers
Reply with a list of terms only, separated by commas. Don't explain.

Text:
{text[:3000]}
"""

                response = None
                text_out = ""

                if model_choice.startswith("FinGPT") and HUGGINGFACE_API_KEY:
                    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
                    response = requests.post(FINGPT_ENDPOINT, headers=headers, json={"inputs": prompt})
                    if response.status_code == 200:
                        terms = response.json()
                        text_out = terms[0].get("generated_text", "") if isinstance(terms, list) else ""
                elif model_choice.startswith("Together") and TOGETHER_API_KEY:
                    headers = {
                        "Authorization": f"Bearer {TOGETHER_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    json_data = {
                        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "max_tokens": 128,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    response = requests.post(TOGETHER_ENDPOINT, headers=headers, json=json_data)
                    try:
                        text_out = response.json()["choices"][0]["message"]["content"]
                    except Exception:
                        text_out = ""

                for term in [t.strip() for t in text_out.split(",") if t.strip()]:
                    found_terms[term].append(i)

        if not found_terms:
            st.warning("No financial terms or fund headers were detected.")
        else:
            term_selection = st.selectbox("Select a financial term or fund section:", sorted(found_terms.keys()))
            if term_selection:
                pages_to_show = found_terms[term_selection]
                st.markdown(f"### Showing {len(pages_to_show)} page(s) for: `{term_selection}`")
                for pg in pages_to_show:
                    st.markdown(f"#### Page {pg + 1} of {len(pages)}")
                    st.text_area("Page Content", pages[pg], height=400)


def run():
    main()
