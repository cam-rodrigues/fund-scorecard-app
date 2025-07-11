import streamlit as st
import pdfplumber
import os
import math
from together import Together
from io import BytesIO

def run():
    st.set_page_config(page_title="AI-Powered Fund Summary", layout="wide")
    st.title("🧠 AI-Powered Fund Summary")
    st.markdown("Upload an MPI-style PDF fund report to generate a structured summary using Together AI.")

    # === Upload Section ===
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="ai_summary_upload")
        with col2:
            st.markdown("### ")
            st.markdown("📝 Supports up to 16,000 characters (~7-9 pages of text).")

    if not uploaded_file:
        st.info("Please upload a PDF report to begin.")
        st.stop()

    # === Metadata Preview ===
    st.markdown("### 🔍 File Details")
    file_size = os.path.getsize(uploaded_file.name) / (1024 * 1024)
    st.markdown(f"- **Name:** {uploaded_file.name}")
    st.markdown(f"- **Size:** {file_size:.2f} MB")

    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        text_pages = [page.extract_text() or "" for page in pdf.pages]
        full_text = "\n".join(text_pages).strip()

    st.markdown(f"- **Pages:** {total_pages}")
    st.markdown(f"- **Extracted Characters:** {len(full_text):,}")

    if not full_text:
        st.error("No extractable text found in this PDF. Try a different file.")
        st.stop()

    # === Optional Preview of Extracted Text ===
    with st.expander("🔎 Preview Extracted Text", expanded=False):
        st.text_area("Raw Extracted Text", full_text[:5000], height=300)

    # === AI Summary Generation ===
    st.markdown("### 📊 AI Summary")

    api_key = st.secrets["together"]["api_key"]
    model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    prompt = f"""You are a financial analyst AI. Summarize the following investment report for a professional advisor.

Focus on:
- Fund performance (returns vs benchmarks)
- Risk-adjusted metrics (Sharpe, Sortino, etc.)
- Expense ratio and turnover
- Asset allocation
- Notable trends or commentary
- Anything unusual or significant

Keep it clear, structured, and professional.

Report:
{full_text[:16000]}"""

    with st.spinner("Analyzing fund report with Together AI..."):
        try:
            client = Together(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            output = response.choices[0].message.content.strip()
            st.markdown(output)

            # === Download Buttons ===
            st.download_button(
                label="📥 Download Summary (.txt)",
                data=output,
                file_name="fund_summary.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"❌ Together AI Error: {e}")
