import streamlit as st
import pdfplumber
import re
import pandas as pd

# Optional: Your own summarizer logic (placeholder)
def summarize_article(text):
    # You can replace this with your actual logic
    return text[:1000] + "..." if len(text) > 1000 else text

# Built-in version of extract_fund_metrics (no external import needed)
def extract_fund_metrics(text):
    lines = text.splitlines()
    fund_rows = []
    current_fund = None

    for line in lines:
        line = line.strip()
        if re.match(r".+\s[A-Z]{4,6}X", line):  # Fund name + ticker pattern
            current_fund = line
            continue
        if current_fund and re.search(r"\d", line) and len(line.split()) >= 6:
            values = re.findall(r"-?\d+\.\d+|\d+", line)
            if values:
                fund_rows.append([current_fund] + values)
                current_fund = None

    if not fund_rows:
        return None

    max_cols = max(len(row) for row in fund_rows)
    columns = ["Fund"] + [f"Metric {i}" for i in range(1, max_cols)]
    df = pd.DataFrame(fund_rows, columns=columns)
    return df

# === Streamlit UI ===
st.set_page_config(page_title="Article Analyzer", layout="wide")
st.title("📰 Article Analyzer")
st.caption("Summarize financial articles and detect embedded fund metrics.")

# Sidebar options
st.sidebar.header("Options")
enable_fund_detection = st.sidebar.checkbox("Enable Fund Metric Detection", value=True)
export_pdf = st.sidebar.button("Export Summary as PDF")

# Input method
input_mode = st.radio("Choose Input Method:", ["Paste Text", "Upload PDF"])
article_text = ""

if input_mode == "Paste Text":
    article_text = st.text_area("Paste Article Text Below", height=300)
elif input_mode == "Upload PDF":
    pdf_file = st.file_uploader("Upload Article PDF", type=["pdf"])
    if pdf_file:
        with pdfplumber.open(pdf_file) as pdf:
            article_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])

# Output
if article_text.strip():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📝 Summary")
        summary = summarize_article(article_text)
        st.write(summary)

    with col2:
        if enable_fund_detection:
            st.subheader("📊 Detected Fund Metrics")
            metrics_df = extract_fund_metrics(article_text)
            if metrics_df is not None:
                st.dataframe(metrics_df, use_container_width=True)
            else:
                st.info("No fund metrics detected.")
        else:
            st.info("Fund detection disabled.")

else:
    st.info("Paste text or upload a PDF to begin.")

# Disclaimer
st.markdown("""
---
⚠️ *This tool is for informational purposes only. Detected metrics may contain errors. Please verify before use.*
""")
