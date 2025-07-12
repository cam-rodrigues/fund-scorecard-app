import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")
    st.write("Hover over each logo to see the source name. Click to open the site.")

    # === Source Data ===
    financial_news = {
        "Bloomberg": ("https://www.bloomberg.com", "https://logo.clearbit.com/bloomberg.com"),
        "WSJ": ("https://www.wsj.com", "https://logo.clearbit.com/wsj.com"),
        "CNBC": ("https://www.cnbc.com", "https://logo.clearbit.com/cnbc.com"),
        "Reuters": ("https://www.reuters.com", "https://logo.clearbit.com/reuters.com"),
        "MarketWatch": ("https://www.marketwatch.com", "https://logo.clearbit.com/marketwatch.com"),
        "Yahoo Finance": ("https://finance.yahoo.com", "https://logo.clearbit.com/yahoo.com"),
    }

    st.subheader("Financial News")
    render_logo_grid_with_tooltips(financial_news)

# === Logo-Only Grid with Hover Tooltips ===
def render_logo_grid_with_tooltips(link_dict, cols_per_row=6):
    keys = list(link_dict.keys())
    for i in range(0, len(keys), cols_per_row):
        row = keys[i:i + cols_per_row]
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            url, logo = link_dict[name]
            with col.container(border=True):
                col.markdown(
                    f"""
                    <a href="{url}" target="_blank">
                        <img src="{logo}" title="{name}" alt="{name}" style="width: 32px; height: 32px; margin: 0.5rem auto; display: block;" />
                    </a>
                    """,
                    unsafe_allow_html=True
                )
