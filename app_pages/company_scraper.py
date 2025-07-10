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

def ai_extract_summary(text):
    prompt = f"""You are a financial analyst assistant. Summarize the key financial performance information from this company report:

{text}"""
    try:
        together_api_key = st.secrets["together"]["api_key"]
        headers = {
            "Authorization": f"Bearer {together_api_key}",
            "Content-Type": "application/json"
        }
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
        return f"Together error: {e}"

def run():
    st.title("Company Financial Crawler")
    st.caption("Enter a public company investor or financial disclosure URL. The tool will scan linked pages and generate clean, structured summaries.")

    url = st.text_input("Company URL", placeholder="https://www.example.com/invest/financials")

    if url:
        with st.spinner("Crawling and processing..."):
            base_html = fetch_html(url)
            if not base_html:
                return

            subpage_urls = extract_financial_links(url, base_html)
            subpage_urls = list(dict.fromkeys(subpage_urls))[:5]

            if not subpage_urls:
                st.warning("No relevant financial subpages were found.")
                return

            st.info(f"{len(subpage_urls)} linked financial subpages identified.")

            results = []
            for sub_url in subpage_urls:
                sub_html = fetch_html(sub_url)
                if not sub_html:
                    continue
                try:
                    tables, text = extract_tables_and_text(sub_html)
                    with st.spinner(f"Generating summary for: {sub_url}"):
                        ai_summary = ai_extract_summary(text)
                    results.append((sub_url, ai_summary, tables))
                except Exception as e:
                    st.error(f"Error parsing {sub_url}: {e}")

        if results:
            st.divider()
            for i, (link, summary, tables) in enumerate(results):
                with st.container():
                    st.subheader(f"Subpage {i+1}")
                    st.markdown(f"[View Original Source]({link})", unsafe_allow_html=True)

                    tab1, tab2 = st.tabs(["Summary", "Extracted Tables"])

                    with tab1:
                        st.markdown("#### Financial Overview")
                        st.markdown(summary)

                    with tab2:
                        if tables:
                            for idx, table in enumerate(tables[:2]):
                                st.markdown(f"Table {idx + 1}")
                                st.dataframe(table)
                        else:
                            st.info("No tabular data was found on this page.")
        else:
            st.warning("No usable financial content was extracted.")
