import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")
    st.markdown("Hover over a logo to see its name. Click to visit the source in a new tab.")

    # Inject CSS for styling
    st.markdown("""
    <style>
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 2.5rem;
    }
    .logo-card {
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #c7d3e0;
        border-radius: 0.75rem;
        background: #f8fbfe;
        height: 120px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .logo-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.07);
        border-color: #aabbd0;
    }
    .logo-card img {
        max-height: 70px;
        max-width: 90px;
        object-fit: contain;
    }
    </style>
    """, unsafe_allow_html=True)

    # Define sources
    sources = {
        "Bloomberg": "https://logo.clearbit.com/bloomberg.com",
        "WSJ": "https://logo.clearbit.com/wsj.com",
        "Reuters": "https://logo.clearbit.com/reuters.com",
        "CNBC": "https://logo.clearbit.com/cnbc.com",
        "FT": "https://logo.clearbit.com/ft.com",
        "Yahoo Finance": "https://logo.clearbit.com/yahoo.com",
        "Forbes": "https://logo.clearbit.com/forbes.com",
        "CNN Business": "https://logo.clearbit.com/cnn.com",
        "MarketWatch": "https://logo.clearbit.com/marketwatch.com",
        "The Economist": "https://logo.clearbit.com/economist.com"
    }

    # Render grid
    html = '<div class="grid">'
    for name, logo_url in sources.items():
        site_url = "https://" + logo_url.replace("https://logo.clearbit.com/", "")
        html += f"""
        <div class="logo-card">
            <a href="{site_url}" target="_blank">
                <img src="{logo_url}" alt="{name}" title="{name}" />
            </a>
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; font-size: 0.9rem;">'
        'Want a new source added? Use the <strong>User Request</strong> tool in the sidebar.'
        '</div>', unsafe_allow_html=True
    )

# Run standalone
if __name__ == "__main__":
    run()
