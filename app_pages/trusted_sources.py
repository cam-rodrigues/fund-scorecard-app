import streamlit as st
import base64
from pathlib import Path

def get_image_as_base64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

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

    hr {
        border: none;
        border-top: 1px solid #c3cfe0;
        margin: 1.25rem auto 0.5rem auto;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("#### Financial News")

    render_sources([
        ("https://www.bloomberg.com", "Bloomberg", "media/bloomberg.png"),
        ("https://www.wsj.com", "Wall Street Journal", "media/wsj.png"),
        ("https://www.cnbc.com", "CNBC", "media/cnbc.png"),
        ("https://www.reuters.com", "Reuters", "media/reuters.png"),
    ])

    st.markdown("#### Investment Research & Tools")

    render_sources([
        ("https://www.morningstar.com", "Morningstar", "media/morningstar.png"),
        ("https://www.ycharts.com", "YCharts", "media/ycharts.png"),
        ("https://www.finviz.com", "Finviz", "media/finviz.png"),
        ("https://www.fidelity.com", "Fidelity", "media/fidelity.png"),
        ("https://www.schwab.com", "Charles Schwab", "media/schwab.png"),
        ("https://www.emoneyadvisor.com", "eMoney Advisor", "media/emoney.png"),
    ])

    st.markdown("#### Government & Policy")

    render_sources([
        ("https://www.sec.gov", "SEC", "media/sec.png"),
        ("https://fred.stlouisfed.org", "FRED (St. Louis Fed)", "media/fred.png"),
        ("https://www.finra.org", "FINRA", "media/finra.png"),
        ("https://www.treasury.gov", "U.S. Treasury", "media/treasury.png"),
    ])

def render_sources(sources):
    st.markdown('<div class="source-grid">', unsafe_allow_html=True)
    for url, name, logo_path in sources:
        encoded = get_image_as_base64(logo_path)
        st.markdown(f"""
        <a href="{url}" target="_blank" class="source-box">
            <img src="data:image/png;base64,{encoded}" alt="{name}" />
            <div class="tooltip">{name}</div>
        </a>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
