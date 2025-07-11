import streamlit as st
import pdfplumber
import re
from together import Together

def extract_fund_sections(full_text):
    fund_sections = []
    lines = full_text.splitlines()
    current_fund = None
    buffer = []

    for line in lines:
        line = line.strip()

        # Match fund headers (customize for your PDFs)
        if re.search(r"(Fund)\s.*(Target|Income|Bond|Index)", line, re.IGNORECASE):
            if current_fund and buffer:
                fund_sections.append((current_fund, "\n".join(buffer)))
                buffer = []
            current_fund = line
        elif current_fund:
            buffer.append(line)

    if current_fund and buffer:
        fund_sections.append((current_fund, "\n".join(buffer)))

    return fund_sections

def run():
    st.set_page_config(page_title="AI Fund Summary (by Fund)", layout="wide")
    st.title("📘 Fund-by-Fund Smart Summary")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if not uploaded_file:
        st.stop()

    # === Extract Text ===
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    fund_sections = extract_fund_sections(full_text)

    if not fund_sections:
        st.error("No fund headers detected.")
        st.stop()

    # === Together API Setup ===
    api_key = st.secrets["together"]["api_key"]
    client = Together(api_key=api_key)
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    for fund_name, fund_text in fund_sections:
        with st.spinner(f"Summarizing {fund_name}..."):
            prompt = f"""
You are a financial analyst. Read this report on the fund "{fund_name}" and extract key insights.
Include performance data, expense ratios, manager tenure, notable risks, and any portfolio composition or benchmark comparisons. Use bullet points.

{fund_text[:16000]}
"""
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                )
                summary = response.choices[0].message.content.strip()
                st.subheader(f"📌 {fund_name}")
                st.markdown(summary)
                st.divider()
            except Exception as e:
                st.error(f"❌ Error summarizing {fund_name}: {e}")
