import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import fitz  # PyMuPDF

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["financial", "results", "earnings", "filing", "report", "quarter", "statement", "10-q", "10-k", "annual"]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

def fetch_html(url):
    try:
        res = requests.get(url, timeout=10, headers=HEADERS)
        return res.text
    except Exception as e:
        st.error(f"Failed to fetch {url}: {e}")
        return ""

def extract_financial_links(base_url, html):
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if any(kw in href.lower() for kw in KEYWORDS):
            full_url = href if href.startswith("http") else requests.compat.urljoin(base_url, href)
            if not any(full_url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                links.add(full_url)
    return list(links)

def extract_tables_and_text(html):
    soup = BeautifulSoup(html, "lxml")
    try:
        tables = pd.read_html(str(soup))
    except Exception:
        tables = []
    return tables, soup.get_text()

def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def ai_extract_summary(text):
    prompt = f"""You are a financial analyst assistant. Summarize the key financial performance information from this company update:\n\n{text}"""
    try:
        api_key = st.secrets["together"]["api_key"]
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        res = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"Together API failed: {res.status_code} - {res.text}"
    except Exception as e:
        return f"Together API error: {e}"

def run():
    st.title("Data Scanner")

    st.markdown("""
    Analyze a public company's investor relations page or upload a PDF to extract financial highlights and generate summaries.
    """)

    mode = st.radio("Choose analysis mode", ["Analyze URL", "Upload PDF"])

    if mode == "Analyze URL":
        url = st.text_input("Enter a company investor page URL", placeholder="https://www.example.com/investor-relations")

        if url:
            with st.spinner("Scanning and processing..."):
                base_html = fetch_html(url)
                if not base_html:
                    return

                subpage_urls = extract_financial_links(url, base_html)
                subpage_urls = list(dict.fromkeys(subpage_urls))[:5]

                if not subpage_urls:
                    st.warning("No relevant financial subpages were found.")
                    return

                st.success(f"Discovered {len(subpage_urls)} financial pages.")
                results = []

                for sub_url in subpage_urls:
                    sub_html = fetch_html(sub_url)
                    if not sub_html:
                        continue
                    try:
                        tables, text = extract_tables_and_text(sub_html)
                        with st.spinner(f"Summarizing: {sub_url}"):
                            ai_summary = ai_extract_summary(text)
                        results.append((sub_url, ai_summary, tables))
                    except Exception as e:
                        st.error(f"Error processing {sub_url}: {e}")

                if results:
                    st.markdown("---")
                    for i, (link, summary, tables) in enumerate(results):
                        with st.expander(f"Page {i+1}: {link}", expanded=False):
                            st.markdown(f"[View original page]({link})", unsafe_allow_html=True)

                            tab1, tab2 = st.tabs(["Summary", "Tables"])
                            with tab1:
                                st.markdown("#### Financial Summary")
                                st.markdown(summary)

                            with tab2:
                                if tables:
                                    for idx, table in enumerate(tables[:2]):
                                        st.markdown(f"**Table {idx+1}**")
                                        st.dataframe(table)
                                else:
                                    st.info("No tables found on this page.")
                else:
                    st.warning("No extractable financial data found.")

    else:  # PDF upload
        uploaded_pdf = st.file_uploader("Upload a financial PDF report", type="pdf")
        if uploaded_pdf:
            with st.spinner("Reading and summarizing PDF..."):
                pdf_text = extract_text_from_pdf(uploaded_pdf)
                if "Error" in pdf_text:
                    st.error(pdf_text)
                    return
                summary = ai_extract_summary(pdf_text)
                st.markdown("### PDF Summary")
                st.markdown(summary)

    st.markdown("---")
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")

