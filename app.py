import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.markdown("""
    Browse grouped links to reputable financial websites. Each source is displayed as a clickable square block with its logo.
    """, unsafe_allow_html=True)

    # === CSS for Grid Layout ===
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
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .source-box:hover {
        background-color: #dce7f8;
        border-color: #a3b9da;
        transform: scale(1.02);
    }

    .source-box img {
        width: 28px;
        height: 28px;
        margin-bottom: 0.5rem;
        object-fit: contain;
    }

    .source-box a {
        text-decoration: none;
        color: inherit;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

    # === Render Function ===
    def render_link_grid(title, links):
        st.subheader(title)
        html = '<div class="source-grid">'
        for name, (url, logo_url) in links.items():
            html += f'''
                <div class="source-box">
                    <a href="{url}" target="_blank">
                        <img src="{logo_url}" alt="{name} logo"/>
                        <div>{name}</div>
                    </a>
                </div>
            '''
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # === Placeholder for Logo Testing ===
    placeholder = "https://via.placeholder.com/28"

    # === Trusted Sources ===
    financial_news = {
        "Bloomberg": ("https://www.bloomberg.com", placeholder),
        "WSJ": ("https://www.wsj.com", placeholder),
        "Reuters": ("https://www.reuters.com", placeholder),
        "Financial Times": ("https://www.ft.com", placeholder),
        "CNBC": ("https://www.cnbc.com", placeholder),
        "MarketWatch": ("https://www.marketwatch.com", placeholder),
        "Yahoo Finance": ("https://finance.yahoo.com", placeholder),
        "The Economist": ("https://www.economist.com", placeholder),
        "Forbes": ("https://www.forbes.com", placeholder),
        "CNN Business": ("https://www.cnn.com/business", placeholder),
    }

    investment_firms = {
        "BlackRock": ("https://www.blackrock.com", placeholder),
        "Vanguard": ("https://www.vanguard.com", placeholder),
        "Fidelity": ("https://www.fidelity.com", placeholder),
        "Charles Schwab": ("https://www.schwab.com", placeholder),
        "J.P. Morgan": ("https://www.jpmorgan.com", placeholder),
        "Goldman Sachs": ("https://www.goldmansachs.com", placeholder),
        "Morgan Stanley": ("https://www.morganstanley.com", placeholder),
    }

    education_research = {
        "Morningstar": ("https://www.morningstar.com", placeholder),
        "Investopedia": ("https://www.investopedia.com", placeholder),
        "Motley Fool": ("https://www.fool.com", placeholder),
        "CFA Institute": ("https://www.cfainstitute.org", placeholder),
        "Wharton": ("https://www.wharton.upenn.edu", placeholder),
        "Harvard Business": ("https://www.hbs.edu", placeholder),
        "MIT Sloan": ("https://mitsloan.mit.edu", placeholder),
        "NBER": ("https://www.nber.org", placeholder),
    }

    government_policy = {
        "SEC": ("https://www.sec.gov", placeholder),
        "Federal Reserve": ("https://www.federalreserve.gov", placeholder),
        "U.S. Treasury": ("https://home.treasury.gov", placeholder),
        "IMF": ("https://www.imf.org", placeholder),
        "World Bank": ("https://www.worldbank.org", placeholder),
        "OECD": ("https://www.oecd.org", placeholder),
    }

    # === Render Sections ===
    render_link_grid("Financial News", financial_news)
    render_link_grid("Major Investment Firms", investment_firms)
    render_link_grid("Education & Research", education_research)
    render_link_grid("Government & Policy", government_policy)
