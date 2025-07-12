import streamlit as st

st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
st.title("📚 Trusted Financial Sources")

st.markdown("""
This page contains grouped links to **reputable financial websites** across news, research, investment, and policy categories.
""")

# === Helper Function
def link_block(title, links):
    st.markdown(f"### {title}")
    for name, url in links.items():
        st.markdown(f"- [{name}]({url})")

# === Link Groups
financial_news = {
    "Bloomberg": "https://www.bloomberg.com",
    "Wall Street Journal": "https://www.wsj.com",
    "Reuters": "https://www.reuters.com",
    "Financial Times": "https://www.ft.com",
    "CNBC": "https://www.cnbc.com",
    "MarketWatch": "https://www.marketwatch.com",
    "Yahoo Finance": "https://finance.yahoo.com",
    "The Economist": "https://www.economist.com",
    "Forbes": "https://www.forbes.com",
    "CNN Business": "https://www.cnn.com/business"
}

investment_firms = {
    "BlackRock": "https://www.blackrock.com",
    "Vanguard": "https://www.vanguard.com",
    "Fidelity": "https://www.fidelity.com",
    "Charles Schwab": "https://www.schwab.com",
    "J.P. Morgan": "https://www.jpmorgan.com",
    "Goldman Sachs": "https://www.goldmansachs.com",
    "Morgan Stanley": "https://www.morganstanley.com",
    "AllianceBernstein": "https://www.alliancebernstein.com"
}

research_and_education = {
    "Morningstar": "https://www.morningstar.com",
    "Investopedia": "https://www.investopedia.com",
    "The Motley Fool": "https://www.fool.com",
    "CFA Institute": "https://www.cfainstitute.org",
    "Wharton School": "https://www.wharton.upenn.edu",
    "Harvard Business School": "https://www.hbs.edu",
    "MIT Sloan": "https://mitsloan.mit.edu",
    "NBER": "https://www.nber.org"
}

government_and_policy = {
    "SEC (U.S. Securities & Exchange Commission)": "https://www.sec.gov",
    "Federal Reserve": "https://www.federalreserve.gov",
    "U.S. Treasury": "https://home.treasury.gov",
    "IMF (International Monetary Fund)": "https://www.imf.org",
    "World Bank": "https://www.worldbank.org",
    "OECD": "https://www.oecd.org"
}

# === Render All Sections
link_block("📈 Financial News & Media", financial_news)
link_block("🏢 Major Investment Firms", investment_firms)
link_block("📚 Education & Research", research_and_education)
link_block("🏛️ Government & Policy", government_and_policy)
