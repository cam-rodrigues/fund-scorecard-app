import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")
    st.write("Hover over any logo to see the source name. Click a logo to visit the site.")

    # Add CSS for hover lift effect
    st.markdown("""
    <style>
    .logo-card {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 1.25rem;
        border: 1px solid #c9d6e5;
        border-radius: 0.75rem;
        background-color: #f8fbfe;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }

    .logo-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
        border-color: #aabdd2;
    }
    </style>
    """, unsafe_allow_html=True)

    # === Source Data ===
    financial_news = {
        "Bloomberg": ("https://www.bloomberg.com", "https://logo.clearbit.com/bloomberg.com"),
        "WSJ": ("https://www.wsj.com", "https://logo.clearbit.com/wsj.com"),
        "CNBC": ("https://www.cnbc.com", "https://logo.clearbit.com/cnbc.com"),
        "Reuters": ("https://www.reuters.com", "https://logo.clearbit.com/reuters.com"),
        "FT": ("https://www.ft.com", "https://logo.clearbit.com/ft.com"),
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
        "AllianceBernstein": ("https://www.alliancebernstein.com", "https://logo.clearbit.com/alliancebernstein.com"),
        "McKinsey": ("https://www.mckinsey.com", "https://logo.clearbit.com/mckinsey.com"),
        "Bain": ("https://www.bain.com", "https://logo.clearbit.com/bain.com"),
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

    # === Sections
    st.subheader("Financial News")
    render_logo_grid(financial_news)

    st.subheader("Investment Firms")
    render_logo_grid(investment_firms)

    st.subheader("Education & Research")
    render_logo_grid(education_research)

    st.subheader("Government & Policy")
    render_logo_grid(government_policy)


# === Grid Renderer with Lift-on-Hover Cards ===
def render_logo_grid(link_dict, cols_per_row=5):
    keys = list(link_dict.keys())
    for i in range(0, len(keys), cols_per_row):
        row = keys[i:i + cols_per_row]
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            url, logo = link_dict[name]
            with col:
                col.markdown(
                    f"""
                    <div class="logo-card">
                        <a href="{url}" target="_blank">
                            <img src="{logo}" title="{name}" alt="{name}" style="width: 96px; height: 96px; object-fit: contain;" />
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
