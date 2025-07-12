import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.markdown("""
    Browse grouped links to reputable financial websites. Each source is displayed as a clickable square block with its logo.
    """, unsafe_allow_html=True)

    # === CSS Styling for Grid Layout with Logo Boxes ===
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

    # === Function to Render Link Grid ===
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

    # === Data ===
    financial_news = {
        "Bloomberg": ("https://www.bloomberg.com", "https://logo.clearbit.com/bloomberg.com"),
        "WSJ": ("https://www.wsj.com", "https://logo.clearbit.com/wsj.com"),
        "Reuters": ("https://www.reuters.com", "https://logo.clearbit.com/reuters.com"),
        "Financial Times": ("https://www.ft.com", "https://logo.clearbit.com/ft.com"),
        "CNBC": ("https://www.cnbc.com", "https://logo.clearbit.com/cnbc.com"),
        "MarketWatch": ("https://www.marketwatch.com", "https://logo.clearbit.com/marketwatch.com"),
        "Yahoo Finance": ("https://finance.yahoo.com", "https://logo.clearbit.com/yahoo.com"),
        "The Economist": ("https://www.economist.com", "https://logo.clearbit.com/economist.com"),
        "Forbes": ("https://www.forbes.com", "https://logo.clearbit.com/forbes.com"),
        "CNN Business": ("https://www.cnn.com/business", "https://logo.clearbit.com/cnn.com"),
    }

    investment_firms = {
        "BlackRock": ("https://www.blackrock.com", "https://logo.clearbit.com/blackrock.com"),
        "Vanguard": ("https://www.vanguard.com", "https://logo.clearbit.com/vanguard.com"),
        "Fidelity": ("https://www.fidelity.com", "https://logo.clearbit.com/fidelity.com"),
        "Charles Schwab": ("https://www.schwab.com", "https://logo.clearbit.com/schwab.com"),
        "J.P. Morgan": ("https://www.jpmorgan.com", "https://logo.clearbit.com/jpmorgan.com"),
        "Goldman Sachs": ("https://www.goldmansachs.com", "https://logo.clearbit.com/goldmansachs.com"),
        "Morgan Stanley": ("https://www.morganstanley.com", "https://logo.clearbit.com/morganstanley.com"),
    }

    education_research = {
        "Morningstar": ("https://www.morningstar.com", "https://logo.clearbit.com/morningstar.com"),
        "Investopedia": ("https://www.investopedia.com", "https://logo.clearbit.com/investopedia.com"),
        "Motley Fool": ("https://www.fool.com", "https://logo.clearbit.com/fool.com"),
        "CFA Institute": ("https://www.cfainstitute.org", "https://logo.clearbit.com/cfainstitute.org"),
        "Wharton": ("https://www.wharton.upenn.edu", "https://logo.clearbit.com/wharton.upenn.edu"),
        "Harvard Business": ("https://www.hbs.edu", "https://logo.clearbit.com/hbs.edu"),
        "MIT Sloan": ("https://mitsloan.mit.edu", "https://logo.clearbit.com/mit.edu"),
        "NBER": ("https://www.nber.org", "https://logo.clearbit.com/nber.org"),
    }

    government_policy = {
        "SEC": ("https://www.sec.gov", "https://logo.clearbit.com/sec.gov"),
        "Federal Reserve": ("https://www.federalreserve.gov", "https://logo.clearbit.com/federalreserve.gov"),
        "U.S. Treasury": ("https://home.treasury.gov", "https://logo.clearbit.com/treasury.gov"),
        "IMF": ("https://www.imf.org", "https://logo.clearbit.com/imf.org"),
        "World Bank": ("https://www.worldbank.org", "https://logo.clearbit.com/worldbank.org"),
        "OECD": ("https://www.oecd.org", "https://logo.clearbit.com/oecd.org"),
    }

    # === Render Sections
    render_link_grid("Financial News", financial_news)
    render_link_grid("Major Investment Firms", investment_firms)
    render_link_grid("Education & Research", education_research)
    render_link_grid("Government & Policy", government_policy)
