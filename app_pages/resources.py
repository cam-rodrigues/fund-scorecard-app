import streamlit as st
import streamlit.components.v1 as components

def run():
    st.set_page_config(page_title="Resources", layout="wide")

    # Shared CSS for everything on the page
    st.markdown("""
    <style>
        .card-container {
            display: flex;
            flex-direction: column;
            gap: 2.2rem;
            margin-top: 2.4rem;
            max-width: 1050px;
            margin-left: auto;
            margin-right: auto;
        }
        .info-card {
            background: #f7fafd;
            border: 1.5px solid #d6e1f3;
            border-radius: 1.6rem;
            box-shadow: 0 2px 12px rgba(66,120,170,0.07);
            padding: 2.15rem 2.3rem 1.3rem 2.3rem;
            margin-bottom: 0.6rem;
            position: relative;
            transition: box-shadow 0.14s;
        }
        .info-card h2 {
            font-size: 1.45rem;
            font-weight: 900;
            color: #164170;
            margin-bottom: 0.45em;
            margin-top: 0;
        }
        .info-card .subtle-tip {
            font-size: 1.03rem;
            color: #48618c;
            margin-bottom: 0.4em;
            margin-top: -0.7em;
        }
        .category-card {
            background: #f9fbfe;
            border: 1px solid #dae5f5;
            border-radius: 1.1rem;
            padding: 1.8rem 1.7rem 1.1rem 1.7rem;
            margin-bottom: 0.5rem;
        }
        .category-card h3 {
            font-size: 1.13rem;
            font-weight: 800;
            color: #215084;
            margin-bottom: 1.1em;
            margin-top: 0.2em;
            letter-spacing: 0.02em;
        }
        .logo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 1.15rem;
            margin-bottom: 0.7rem;
        }
        .logo-box {
            background: #f0f4fa;
            border: 1px solid #cbd5e1;
            border-radius: 0.75rem;
            padding: 0.7rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.19s, border-color 0.19s;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            height: 85px;
        }
        .logo-box:hover {
            transform: scale(1.055);
            border-color: #285593;
            cursor: pointer;
        }
        .logo-box img {
            max-width: 80%;
            max-height: 62px;
            height: auto;
        }
        .divider {
            border: none;
            border-top: 1.2px solid #d6e2ee;
            margin: 1.4rem 0 1.8rem 0;
        }
        .bottom-callout {
            margin-top: 1.8rem;
            padding: 1.1rem 1.3rem 1.1rem 1.3rem;
            background: #f6f9fd;
            border: 1px solid #d6e2ee;
            border-radius: 0.7rem;
            font-size: 0.98rem;
            color: #37445a;
        }
    </style>
    """, unsafe_allow_html=True)

    # Trusted-site categories
    categories = {
        "Financial News": [
            {"name": "Bloomberg", "url": "https://www.bloomberg.com", "logo": "https://logo.clearbit.com/bloomberg.com"},
            {"name": "Yahoo Finance", "url": "https://finance.yahoo.com", "logo": "https://logo.clearbit.com/yahoo.com"},
            {"name": "CNBC", "url": "https://www.cnbc.com", "logo": "https://logo.clearbit.com/cnbc.com"},
            {"name": "MarketWatch", "url": "https://www.marketwatch.com", "logo": "https://logo.clearbit.com/marketwatch.com"},
            {"name": "Barron's", "url": "https://www.barrons.com", "logo": "https://logo.clearbit.com/barrons.com"},
            {"name": "Reuters", "url": "https://www.reuters.com/finance", "logo": "https://logo.clearbit.com/reuters.com"},
            {"name": "The Wall Street Journal", "url": "https://www.wsj.com", "logo": "https://logo.clearbit.com/wsj.com"},
            {"name": "Forbes", "url": "https://www.forbes.com", "logo": "https://logo.clearbit.com/forbes.com"},
            {"name": "Financial Times", "url": "https://www.ft.com", "logo": "https://logo.clearbit.com/ft.com"},
        ],
        "Market Data & Research": [
            {"name": "Morningstar", "url": "https://www.morningstar.com", "logo": "https://logo.clearbit.com/morningstar.com"},
            {"name": "TradingView", "url": "https://www.tradingview.com", "logo": "https://logo.clearbit.com/tradingview.com"},
            {"name": "Seeking Alpha", "url": "https://seekingalpha.com", "logo": "https://logo.clearbit.com/seekingalpha.com"},
            {"name": "Zacks", "url": "https://www.zacks.com", "logo": "https://logo.clearbit.com/zacks.com"},
            {"name": "Finviz", "url": "https://finviz.com", "logo": "https://logo.clearbit.com/finviz.com"},
            {"name": "Barchart", "url": "https://www.barchart.com", "logo": "https://logo.clearbit.com/barchart.com"},
            {"name": "YCharts", "url": "https://ycharts.com", "logo": "https://logo.clearbit.com/ycharts.com"},
            {"name": "MacroTrends", "url": "https://www.macrotrends.net", "logo": "https://logo.clearbit.com/macrotrends.net"},
        ],
        "Investment Firms": [
            {"name": "Fidelity", "url": "https://www.fidelity.com", "logo": "https://logo.clearbit.com/fidelity.com"},
            {"name": "Vanguard", "url": "https://investor.vanguard.com", "logo": "https://logo.clearbit.com/vanguard.com"},
            {"name": "Charles Schwab", "url": "https://www.schwab.com", "logo": "https://logo.clearbit.com/schwab.com"},
            {"name": "TD Ameritrade", "url": "https://www.tdameritrade.com", "logo": "https://logo.clearbit.com/tdameritrade.com"},
            {"name": "J.P. Morgan", "url": "https://www.jpmorgan.com", "logo": "https://logo.clearbit.com/jpmorgan.com"},
            {"name": "Envestnet", "url": "https://www.envestnet.com", "logo": "https://logo.clearbit.com/envestnet.com"},
            {"name": "T. Rowe Price", "url": "https://www.troweprice.com", "logo": "https://logo.clearbit.com/troweprice.com"},
            {"name": "Edward Jones", "url": "https://www.edwardjones.com", "logo": "https://logo.clearbit.com/edwardjones.com"},
        ],
        "Government & Regulatory": [
            {"name": "SEC", "url": "https://www.sec.gov", "logo": "https://logo.clearbit.com/sec.gov"},
            {"name": "FINRA", "url": "https://www.finra.org", "logo": "https://logo.clearbit.com/finra.org"},
            {"name": "FDIC", "url": "https://www.fdic.gov", "logo": "https://logo.clearbit.com/fdic.gov"},
            {"name": "Federal Reserve", "url": "https://www.federalreserve.gov", "logo": "https://logo.clearbit.com/federalreserve.gov"},
            {"name": "CFPB", "url": "https://www.consumerfinance.gov", "logo": "https://logo.clearbit.com/consumerfinance.gov"},
            {"name": "IRS", "url": "https://www.irs.gov", "logo": "https://logo.clearbit.com/irs.gov"},
        ],
        "Education & Tools": [
            {"name": "Investopedia", "url": "https://www.investopedia.com", "logo": "https://logo.clearbit.com/investopedia.com"},
            {"name": "NerdWallet", "url": "https://www.nerdwallet.com", "logo": "https://logo.clearbit.com/nerdwallet.com"},
            {"name": "eMoney", "url": "https://emoneyadvisor.com", "logo": "https://logo.clearbit.com/emoneyadvisor.com"},
            {"name": "Khan Academy", "url": "https://www.khanacademy.org/economics-finance-domain", "logo": "https://logo.clearbit.com/khanacademy.org"},
            {"name": "SmartAsset", "url": "https://smartasset.com", "logo": "https://logo.clearbit.com/smartasset.com"},
            {"name": "Bankrate", "url": "https://www.bankrate.com", "logo": "https://logo.clearbit.com/bankrate.com"},
            {"name": "Mint", "url": "https://mint.intuit.com", "logo": "https://logo.clearbit.com/mint.intuit.com"},
        ],
    }

    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    # Title and tip card
    st.markdown('''
        <div class="info-card">
            <h2>Resources</h2>
            <div class="subtle-tip">Click any logo below to open the site in a new tab.</div>
        </div>
    ''', unsafe_allow_html=True)

    # Each category in a card with a grid
    for i, (category, sites) in enumerate(categories.items()):
        st.markdown(f'''
            <div class="category-card">
                <h3>{category}</h3>
                <div class="logo-grid">
        ''', unsafe_allow_html=True)

        for site in sites:
            # Note: Using components.html to allow <a target="_blank">
            logo_html = (
                f'<a href="{site["url"]}" target="_blank" class="logo-box">'
                f'  <img src="{site["logo"]}" alt="{site["name"]} logo" title="{site["name"]}">'
                f'</a>'
            )
            components.html(logo_html, height=92, scrolling=False)

        st.markdown('</div></div>', unsafe_allow_html=True)

        if i < len(categories) - 1:
            st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Bottom callout
    st.markdown('''
        <div class="bottom-callout">
            Looking for a site that’s not listed here?<br>
            Please submit a <strong>user request</strong> and we’ll add it to the trusted resources.
        </div>
    ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
