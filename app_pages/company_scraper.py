# Construct the new AI-enhanced scraper script with both raw + GPT-extracted summaries
upgraded_scraper_code = """
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai

openai.api_key = st.secrets["openai"]["api_key"]

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = [
    "financial", "results", "earnings", "filing", "report",
    "quarter", "10-q", "10-k", "annual", "statement", "balance", "income"
]
SKIP_EXTENSIONS = [".pdf", ".xls", ".xlsx", ".doc", ".docx"]

def fetch_html(url):
    try:
        res = requests.get(url, timeout=10, headers=HEADERS)
        return res.text
    except Exception as e:
        st.error(f"❌ Failed to fetch {url}: {e}")
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
    prompt = f\"\"\"
You are a financial analyst assistant. Read this text and extract the key financial performance details.
Summarize earnings, EBITDA, cash flow, revenue, income, margins, or debt if mentioned.
Respond clearly in bullet points or short paragraphs.

{text}
\"\"\"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ OpenAI failed: {e}"

def run():
    st.title("📡 Company Financial Crawler + ✨ AI Summary")

    url = st.text_input("🔗 Enter investor/financial website")

    if url:
        with st.spinner("🔍 Crawling site..."):
            base_html = fetch_html(url)
            if not base_html:
                return

            subpage_urls = extract_financial_links(url, base_html)
            subpage_urls = list(dict.fromkeys(subpage_urls))[:10]

            if not subpage_urls:
                st.warning("No financial subpages found.")
                return

            st.info(f"🔗 Found {len(subpage_urls)} subpages. Scanning...")

            results = []
            for sub_url in subpage_urls:
                if any(sub_url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue

                st.markdown(f"**Scanning:** {sub_url}")
                sub_html = fetch_html(sub_url)
                if not sub_html:
                    continue
                try:
                    tables, text = extract_tables_and_text(sub_html)
                    ai_summary = ai_extract_summary(text)
                    results.append((sub_url, ai_summary, text[:3000]))  # limit raw preview
                except Exception as e:
                    st.error(f"❌ Error parsing {sub_url}: {e}")

        if results:
            for i, (link, summary, raw) in enumerate(results):
                with st.expander(f"📄 Page {i+1}: {link}"):
                    st.markdown("### ✨ AI Summary")
                    st.markdown(summary)

                    st.markdown("### 📄 Raw Text Snapshot")
                    st.code(raw[:2000])
        else:
            st.warning("No usable financial data found.")
"""

# Save the upgraded script
updated_path = os.path.join(extract_dir, 'fydsync-main', 'app_pages', 'company_scraper.py')
with open(updated_path, 'w', encoding='utf-8') as f:
    f.write(upgraded_scraper_code.strip())

updated_path
