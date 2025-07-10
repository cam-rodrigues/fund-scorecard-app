
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

    if ticker:
        st.markdown(f"### Results for `{ticker}`")
        for name, url in get_links(ticker).items():
            st.markdown(f"- [{name}]({url})")
