import streamlit as st
import streamlit.components.v1 as components

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.markdown("#### Financial News")
    render_sources([
        ("https://www.bloomberg.com", "Bloomberg", "https://upload.wikimedia.org/wikipedia/commons/3/3d/Bloomberg_Market_Data_logo.png"),
        ("https://www.wsj.com", "Wall Street Journal", "https://static.wsj.net/wsj-logo.png"),
        ("https://www.cnbc.com", "CNBC", "https://upload.wikimedia.org/wikipedia/en/2/20/CNBC_logo.png"),
        ("https://www.reuters.com", "Reuters", "https://s3-symbol-logo.tradingview.com/reuters--600.png"),
    ], height=500)

    st.markdown("#### Investment Research & Tools")
    render_sources([
        ("https://www.morningstar.com", "Morningstar", "https://upload.wikimedia.org/wikipedia/en/thumb/e/e3/Morningstar_Logo.png/320px-Morningstar_Logo.png"),
        ("https://www.ycharts.com", "YCharts", "https://assets-global.website-files.com/615c6125781dd69aafe19db1/618ac0d2f87c9637e3c3aa3e_ycharts-logo.png"),
        ("https://www.finviz.com", "Finviz", "https://finviz.com/images/logo01.png"),
        ("https://www.fidelity.com", "Fidelity", "https://upload.wikimedia.org/wikipedia/en/6/65/Fidelity_Investments_logo.png"),
        ("https://www.schwab.com", "Charles Schwab", "https://www.schwab.com/etc.clientlibs/settings/wcm/designs/schwab/clientlibs/clientlib-site/resources/img/logo.png"),
        ("https://www.emoneyadvisor.com", "eMoney Advisor", "https://media.licdn.com/dms/image/C560BAQHKdJObRzN4Ew/company-logo_200_200/0/1630571410247/emoney_advisor_logo.png"),
    ], height=600)

    st.markdown("#### Government & Policy")
    render_sources([
        ("https://www.sec.gov", "SEC", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Seal_of_the_United_States_Securities_and_Exchange_Commission.svg/600px-Seal_of_the_United_States_Securities_and_Exchange_Commission.svg.png"),
        ("https://fred.stlouisfed.org", "FRED (St. Louis Fed)", "https://fred.stlouisfed.org/~/media/Images/fred/fred-logo-blue.svg"),
        ("https://www.finra.org", "FINRA", "https://s3-symbol-logo.tradingview.com/finra--600.png"),
        ("https://www.treasury.gov", "U.S. Treasury", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Seal_of_the_United_States_Department_of_the_Treasury.svg/600px-Seal_of_the_United_States_Department_of_the_Treasury.svg.png"),
    ], height=550)


def render_sources(sources, height=500):
    html = '<div class="source-grid">'
    for url, name, logo_url in sources:
        html += f"""
        <a href="{url}" target="_blank" class="source-box" title="{name}">
            <img src="{logo_url}" alt="{name}" />
        </a>
        """
    html += '</div>'

    components.html(f"""
    <html>
    <head>
    <style>
    .source-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 1.2rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }}
    .source-box {{
        background-color: #f0f4fa;
        border: 1px solid #d4ddec;
        border-radius: 0.75rem;
        padding: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100px;
        transition: transform 0.2s ease-in-out;
    }}
    .source-box:hover {{
        transform: translateY(-4px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    .source-box img {{
        max-width: 100%;
        max-height: 60px;
        object-fit: contain;
    }}
    </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """, height=height, scrolling=False)
