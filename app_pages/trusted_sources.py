import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.markdown("""
    Browse trustworthy financial websites below. Click any logo to open the site in a new tab.
    """, unsafe_allow_html=False)

    # Style for the logo grid layout
    st.markdown("""
    <style>
    .logo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 1.5rem;
        padding-top: 1.5rem;
    }

    .logo-box {
        background: #f0f4fa;
        border-radius: 0.75rem;
        padding: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        height: 90px;
    }

    .logo-box:hover {
        transform: scale(1.06);
        cursor: pointer;
    }

    .logo-box img {
        max-width: 80%;
        max-height: 60px;
        height: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    sources = [
        {"name": "Bloomberg", "url": "https://www.bloomberg.com", "logo": "https://logo.clearbit.com/bloomberg.com"},
        {"name": "Morningstar", "url": "https://www.morningstar.com", "logo": "https://logo.clearbit.com/morningstar.com"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com", "logo": "https://logo.clearbit.com/yahoo.com"},
        {"name": "CNBC", "url": "https://www.cnbc.com", "logo": "https://logo.clearbit.com/cnbc.com"},
        {"name": "Fidelity", "url": "https://www.fidelity.com", "logo": "https://logo.clearbit.com/fidelity.com"},
        {"name": "Investopedia", "url": "https://www.investopedia.com", "logo": "https://logo.clearbit.com/investopedia.com"},
        {"name": "SEC", "url": "https://www.sec.gov", "logo": "https://logo.clearbit.com/sec.gov"},
        {"name": "FINRA", "url": "https://www.finra.org", "logo": "https://logo.clearbit.com/finra.org"},
        {"name": "MarketWatch", "url": "https://www.marketwatch.com", "logo": "https://logo.clearbit.com/marketwatch.com"},
        {"name": "Barron's", "url": "https://www.barrons.com", "logo": "https://logo.clearbit.com/barrons.com"},
        {"name": "eMoney", "url": "https://emoneyadvisor.com", "logo": "https://logo.clearbit.com/emoneyadvisor.com"},
        {"name": "Envestnet", "url": "https://www.envestnet.com", "logo": "https://logo.clearbit.com/envestnet.com"},
    ]

    # Render the full HTML grid as one block
    grid_html = '<div class="logo-grid">'
    for source in sources:
        grid_html += f'''
        <a href="{source["url"]}" target="_blank" class="logo-box">
            <img src="{source["logo"]}" alt="{source["name"]} logo" title="{source["name"]}">
        </a>
        '''
    grid_html += '</div>'

    st.markdown(grid_html, unsafe_allow_html=True)
