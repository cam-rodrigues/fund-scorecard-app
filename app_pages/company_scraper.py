import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["financial", "results", "earnings", "filing", "report", "quarter", "statement", "10-q", "10-k", "annual"]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

def fetch_html(url):
    try:
        res = requests.get(url, timeout=10, headers=HEADERS)
        return res.text
    except Exception:
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

def ai_extract_summary(text):
    prompt = f"""Summarize the main financial results and business highlights:

{text}"""
    try:
        key = st.secrets["together"]["api_key"]
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
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
            return "Summary not available."
    except Exception:
        return "Summary failed to generate."

def run():
    st.title("Company Financial Crawler")

    url = st.text_input("Investor Relations URL")

    show_tables = st.checkbox("Show financial tables (if available)", value=True)

    if url:
        with st.spinner("Scanning website..."):
            html = fetch_html(url)
            if not html:
                st.error("Failed to load the page.")
                return

            links = extract_financial_links(url, html)[:5]
            if not links:
                st.warning("No relevant subpages found.")
                return

            for i, link in enumerate(links):
                sub_html = fetch_html(link)
                if not sub_html:
                    continue
                tables, text = extract_tables_and_text(sub_html)
                summary = ai_extract_summary(text)

                with st.container():
                    st.markdown(f"### Page {i+1}")
                    st.markdown(f"[View Original Page]({link})", unsafe_allow_html=True)

                    st.markdown("#### Summary")
                    st.markdown(f"<div style='max-height:300px; overflow-y:auto; background:#f9f9f9; padding:10px; border:1px solid #ddd;'>{summary}</div>", unsafe_allow_html=True)

                    if show_tables and tables:
                        for idx, table in enumerate(tables[:1]):
                            st.markdown(f"**Extracted Table {idx + 1}**")
                            st.dataframe(table, use_container_width=True)
