import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Company Lookup", layout="centered")
st.title("🔍 Company Ticker Info Finder")

ticker = st.text_input("Enter a company ticker symbol (e.g., AAPL, TSLA, MSFT):").upper()

def get_summary_links(ticker):
    links = {}

    # Yahoo Finance
    links["Yahoo Finance"] = f"https://finance.yahoo.com/quote/{ticker}"

    # Google News search
    links["Google News"] = f"https://www.google.com/search?q={ticker}+stock&tbm=nws"

    # Seeking Alpha (no scraping, just linking)
    links["Seeking Alpha"] = f"https://seekingalpha.com/symbol/{ticker}"

    # SEC Filings
    links["SEC Filings"] = f"https://www.sec.gov/edgar/browse/?CIK={ticker}&owner=exclude"

    # Attempt to find Investor Relations page via search
    try:
        query = f"{ticker} investor relations"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        results = soup.find_all("a")
        ir_links = [a["href"] for a in results if "/url?q=" in a["href"] and "investor" in a["href"]]
        if ir_links:
            links["Investor Relations"] = ir_links[0].split("/url?q=")[1].split("&")[0]
    except Exception:
        pass

    return links

if ticker:
    st.markdown(f"### 🔗 Results for `{ticker}`:")
    links = get_summary_links(ticker)

    for name, url in links.items():
        st.markdown(f"- [{name}]({url})")
