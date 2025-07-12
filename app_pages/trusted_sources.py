import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.markdown("""
    <style>
    .source-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 1.2rem;
        margin-top: 1.5rem;
        margin-bottom: 2rem;
    }

    .source-box {
        background-color: #f0f4fa;
        border: 1px solid #d4ddec;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
        transition: transform 0.2s ease-in-out;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        cursor: pointer;
        position: relative;
    }

    .source-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .source-box img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 0 auto;
    }

    .tooltip {
        position: absolute;
        bottom: -2.2rem;
        left: 50%;
        transform: translateX(-50%);
        background-color: #1a2a44;
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 0.4rem;
        font-size: 0.75rem;
        white-space: nowrap;
        display: none;
        z-index: 5;
    }

    .source-box:hover .tooltip {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("#### Financial News")
    render_sources([
        ("https://www.bloomberg.com", "Bloomberg", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Bloomberg_logo.svg/2560px-Bloomberg_logo.svg.png"),
        ("https://www.wsj.com", "Wall Street Journal", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/The_Wall_Street_Journal_Logo.svg/1280px-The_Wall_Street_Journal_Logo.svg.png"),
        ("https://www.cnbc.com", "CNBC", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/CNBC_logo.svg/2560px-CNBC_logo.svg.png"),
        ("https://www.reuters.com", "Reuters", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Reuters-Logo.svg/2560px-Reuters-Logo.svg.png"),
    ])

    st.markdown("#### Investment Research & Tools")
    render_sources([
        ("https://www.morningstar.com", "Morningstar", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Morningstar_Logo.svg/2560px-Morningstar_Logo.svg.png"),
        ("https://www.ycharts.com", "YCharts", "https://assets-global.website-files.com/615c6125781dd69aafe19db1/618ac0d2f87c9637e3c3aa3e_ycharts-logo.png"),
        ("https://www.finviz.com", "Finviz", "https://finviz.com/favicon.ico"),
        ("https://www.fidelity.com", "Fidelity", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Fidelity_Investments_logo.svg/2560px-Fidelity_Investments_logo.svg.png"),
        ("https://www.schwab.com", "Charles Schwab", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Charles_Schwab_Corporation_logo.svg/2560px-Charles_Schwab_Corporation_logo.svg.png"),
        ("https://www.emoneyadvisor.com", "eMoney Advisor", "https://www.emoneyadvisor.com/wp-content/themes/emoney-2020/assets/images/emoney_logo.svg"),
    ])

    st.markdown("#### Government & Policy")
    render_sources([
        ("https://www.sec.gov", "SEC", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Seal_of_the_United_States_Securities_and_Exchange_Commission.svg/2048px-Seal_of_the_United_States_Securities_and_Exchange_Commission.svg.png"),
        ("https://fred.stlouisfed.org", "FRED (St. Louis Fed)", "https://fred.stlouisfed.org/~/media/Images/fred/fred-logo-blue.svg"),
        ("https://www.finra.org", "FINRA", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/FINRA_logo.svg/2560px-FINRA_logo.svg.png"),
        ("https://www.treasury.gov", "U.S. Treasury", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Seal_of_the_United_States_Department_of_the_Treasury.svg/2048px-Seal_of_the_United_States_Department_of_the_Treasury.svg.png"),
    ])


def render_sources(sources):
    st.markdown('<div class="source-grid">', unsafe_allow_html=True)
    for url, name, logo_url in sources:
        st.markdown(f"""
        <a href="{url}" target="_blank" class="source-box">
            <img src="{logo_url}" alt="{name}" />
            <div class="tooltip">{name}</div>
        </a>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
