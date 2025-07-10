import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os

def run():
    st.title("🔍 Company Ticker Info Finder")

    # === Ticker input
    ticker = st.text_input("Enter a stock ticker symbol (e.g. AAPL, TSLA, MSFT):").upper()

    # === Optional: static mapping (can later connect to API or CSV)
    known_names = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "TSLA": "Tesla Inc.",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "NVDA": "NVIDIA Corporation",
        "JPM": "JPMorgan Chase & Co.",
        "META": "Meta Platforms Inc.",
        "BRK.B": "Berkshire Hathaway Inc.",
    }

    def get_company_name(ticker):
        return known_names.get(ticker, f"{ticker} (Company name not found)")

    def get_links(ticker):
        links = {
            "Yahoo Finance": f"https://finance.yahoo.com/quote/{ticker}",
            "Google News": f"https://www.google.com/search?q={ticker}+stock&tbm=nws",
            "Seeking Alpha": f"https://seekingalpha.com/symbol/{ticker}",
            "SEC Filings": f"https://www.sec.gov/edgar/browse/?CIK={ticker}&owner=exclude"
        }

        try:
            # Try to guess the Investor Relations link
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

    @st.cache_data(show_spinner=False)
    def fetch_preview(url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, timeout=5, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                return desc["content"].strip()
        except:
            pass
        return None

    # PDF helper
    def generate_pdf(company_name, links, previews):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt=f"{company_name} — Company Info Summary", ln=True, align="C")

        pdf.set_font("Arial", size=11)
        for name, url in links.items():
            pdf.ln(6)
            pdf.set_text_color(0, 0, 180)
            pdf.set_font(style="B")
            pdf.cell(0, 10, f"{name}: {url}", ln=True)
            preview = previews.get(name)
            if preview:
                pdf.set_text_color(0, 0, 0)
                pdf.set_font(style="")
                pdf.multi_cell(0, 8, f"{preview}")

        output_path = "/mnt/data/company_summary.pdf"
        pdf.output(output_path)
        return output_path

    if ticker:
        company_name = get_company_name(ticker)
        st.markdown(f"### 🔗 Results for **{company_name}**")
        with st.spinner("Fetching links and previews..."):
            links = get_links(ticker)
            previews = {name: fetch_preview(url) for name, url in links.items()}

        for name, url in links.items():
            with st.container():
                st.markdown(f"#### [{name}]({url})")
                preview = previews.get(name)
                if preview:
                    st.write(preview)

        # === PDF Export
        if st.button("📄 Export summary as PDF"):
            pdf_path = generate_pdf(company_name, links, previews)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name=f"{ticker}_summary.pdf", mime="application/pdf")
