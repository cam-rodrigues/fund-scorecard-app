import streamlit as st
import streamlit.components.v1 as components

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.markdown("""
    Browse trustworthy financial websites below. Click any logo to open the site in a new tab.
    """, unsafe_allow_html=True)

    # === Categories with Logos ===
    categories = {
        "Financial News": [
            {"name": "Bloomberg", "url": "https://www.bloomberg.com", "logo": "https://logo.clearbit.com/bloomberg.com"},
            {"name": "Yahoo Finance", "url": "https://finance.yahoo.com", "logo": "https://logo.clearbit.com/yahoo.com"},
            {"name": "CNBC", "url": "https://www.cnbc.com", "logo": "https://logo.clearbit.com/cnbc.com"},
            {"name": "MarketWatch", "url": "https://www.marketwatch.com", "logo": "https://logo.clearbit.com/marketwatch.com"},
            {"name": "Barron's", "url": "https://www.barrons.com", "logo": "https://logo.clearbit.com/barrons.com"},
            {"name": "Reuters", "url": "https://www.reuters.com/finance", "logo": "https://logo.clearbit.com/reuters.com"},
            {"name": "The Wall Street Journal", "url": "https://www.wsj.com", "logo": "https://logo.clearbit.com/wsj.com"},
        ],
        "Market Data & Research": [
            {"name": "Morningstar", "url": "https://www.morningstar.com", "logo": "https://logo.clearbit.com/morningstar.com"},
            {"name": "TradingView", "url": "https://www.tradingview.com", "logo": "https://logo.clearbit.com/tradingview.com"},
            {"name": "Seeking Alpha", "url": "https://seekingalpha.com", "logo": "https://logo.clearbit.com/seekingalpha.com"},
            {"name": "Zacks", "url": "https://www.zacks.com", "logo": "https://logo.clearbit.com/zacks.com"},
            {"name": "Finviz", "url": "https://finviz.com", "logo": "https://logo.clearbit.com/finviz.com"},
        ],
        "Investment Firms": [
            {"name": "Fidelity", "url": "https://www.fidelity.com", "logo": "https://logo.clearbit.com/fidelity.com"},
            {"name": "Vanguard", "url": "https://investor.vanguard.com", "logo": "https://logo.clearbit.com/vanguard.com"},
            {"name": "Charles Schwab", "url": "https://www.schwab.com", "logo": "https://logo.clearbit.com/schwab.com"},
            {"name": "TD Ameritrade", "url": "https://www.tdameritrade.com", "logo": "https://logo.clearbit.com/tdameritrade.com"},
            {"name": "J.P. Morgan", "url": "https://www.jpmorgan.com", "logo": "https://logo.clearbit.com/jpmorgan.com"},
            {"name": "Envestnet", "url": "https://www.envestnet.com", "logo": "https://logo.clearbit.com/envestnet.com"},
        ],
        "Government & Regulatory": [
            {"name": "SEC", "url": "https://www.sec.gov", "logo": "https://logo.clearbit.com/sec.gov"},
            {"name": "FINRA", "url": "https://www.finra.org", "logo": "https://logo.clearbit.com/finra.org"},
            {"name": "FDIC", "url": "https://www.fdic.gov", "logo": "https://logo.clearbit.com/fdic.gov"},
            {"name": "Federal Reserve", "url": "https://www.federalreserve.gov", "logo": "https://logo.clearbit.com/federalreserve.gov"},
        ],
        "Education & Tools": [
            {"name": "Investopedia", "url": "https://www.investopedia.com", "logo": "https://logo.clearbit.com/investopedia.com"},
            {"name": "NerdWallet", "url": "https://www.nerdwallet.com", "logo": "https://logo.clearbit.com/nerdwallet.com"},
            {"name": "eMoney", "url": "https://emoneyadvisor.com", "logo": "https://logo.clearbit.com/emoneyadvisor.com"},
            {"name": "Khan Academy", "url": "https://www.khanacademy.org/economics-finance-domain", "logo": "https://logo.clearbit.com/khanacademy.org"},
        ],
    }

    # === Inline CSS (included with every grid block)
    css = """
    <style>
        .category-header {
            font-size: 1.3rem;
            font-weight: 700;
            color: #102542;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
        }

        .logo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .logo-box {
            background: #f0f4fa;
            border: 1px solid #cbd5e1;
            border-radius: 0.75rem;
            padding: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s ease, border-color 0.2s;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            height: 90px;
        }

        .logo-box:hover {
            transform: scale(1.06);
            border-color: #1c2e4a;
            cursor: pointer;
        }

        .logo-box img {
            max-width: 80%;
            max-height: 60px;
            height: auto;
        }
    </style>
    """

    # === Render Each Category
    for category, sites in categories.items():
        st.markdown(f'<div class="category-header">{category}</div>', unsafe_allow_html=True)

        # Inline CSS + HTML for each block
        html_block = css + '<div class="logo-grid">'
        for site in sites:
            html_block += f'''
                <a href="{site["url"]}" target="_blank" class="logo-box">
                    <img src="{site["logo"]}" alt="{site["name"]} logo" title="{site["name"]}">
                </a>
            '''
        html_block += '</div>'

        components.html(html_block, height=160 + (len(sites) // 4 + 1) * 120, scrolling=False)
