import streamlit as st
import requests
from bs4 import BeautifulSoup

def run():
    st.title("Company Ticker Info Finder")
    ticker = st.text_input("Enter a stock ticker symbol (e.g. AAPL, TSLA, MSFT):").upper()

    def get_links(ticker):
        links = {
            "Yahoo Finance": f"https://finance.yahoo.com/quote/{ticker}",
            "Google News": f"https://www.google.com/search?q={ticker}+stock&tbm=nws",
            "Seeking Alpha": f"https://seekingalpha.com/symbol/{ticker}",
            "SEC Filings": f"https://www.sec.gov/edgar/browse/?CIK={ticker}&owner=exclude"
        }

        try:
            # Investor Relations (best guess via Google)
            query = f"{ticker} investor relations"
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            anchors = soup.find_all("a")
            ir_links = [a["href"] for a in anchors if "/url?q=" in a["href"] and "investor" in a["href"]]
            if ir_links:
                links["Investor Relations"] = ir_links[0].split("/url?q=")[1].split("&")[0]
        except Exception:
            pass

        return links

    def fetch_preview(url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, timeout=4, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                return desc["content"].strip()
        except:
            pass
        return None

    if ticker:
        st.markdown(f"### Results for `{ticker}`")

        with st.spinner("Fetching links..."):
            links = get_links(ticker)

        for name, url in links.items():
            with st.container():
                st.markdown(f"#### [{name}]({url})")
                preview = fetch_preview(url)
                if preview:
                    st.write(preview)
