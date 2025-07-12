import streamlit as st

st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
st.title("Trusted Financial Sources")

st.markdown("""
Browse grouped links to **reputable financial websites**. Each source is shown as a clickable square block for easier scanning.
""", unsafe_allow_html=True)

# === Define CSS for square blocks ===
st.markdown("""
<style>
.source-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
    margin-bottom: 2.5rem;
}

.source-box {
    background-color: #f0f4fa;
    border: 1px solid #d4ddec;
    border-radius: 0.5rem;
    padding: 1rem;
    text-align: center;
    transition: 0.2s ease-in-out;
    font-weight: 600;
    color: #1a2a44;
}

.source-box:hover {
    background-color: #dce7f8;
    border-color: #a3b9da;
    transform: scale(1.02);
}

.source-box a {
    text-decoration: none;
    color: inherit;
    display: block;
}
</style>
""", unsafe_allow_html=True)

# === Helper Function to Render Grid ===
def render_link_grid(title, links):
    st.markdown(f"## {title}")
    html = '<div class="source-grid">'
    for name, url in links.items():
        html += f'<div class="source-box"><a href="{url}" target="_blank">{name}</a></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# === Link Groups
financial_news = {
    "Bloomberg": "https://www.bloomberg.com",
    "WSJ": "https://www.wsj.com",
    "Reuters": "https://www.reuters.com",
    "FT": "https://www.ft.com",
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
    "Morgan Stanley": "https://www.morganstanley.com"
}

education_research = {
    "Morningstar": "https://www.morningstar.com",
    "Investopedia": "https://www.investopedia.com",
    "Motley Fool": "https://www.fool.com",
    "CFA Institute": "https://www.cfainstitute.org",
    "Wharton": "https://www.wharton.upenn.edu",
    "Harvard Business": "https://www.hbs.edu",
    "MIT Sloan": "https://mitsloan.mit.edu",
    "NBER": "https://www.nber.org"
}

government_policy = {
    "SEC": "https://www.sec.gov",
    "Federal Reserve": "https://www.federalreserve.gov",
    "U.S. Treasury": "https://home.treasury.gov",
    "IMF": "https://www.imf.org",
    "World Bank": "https://www.worldbank.org",
    "OECD": "https://www.oecd.org"
}

# === Render All Blocks
render_link_grid("Financial News", financial_news)
render_link_grid("Major Investment Firms", investment_firms)
render_link_grid("Education & Research", education_research)
render_link_grid("Government & Policy", government_policy)
