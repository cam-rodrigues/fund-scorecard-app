import streamlit as st

def run():
    st.set_page_config(page_title="Trusted Financial Sources", layout="wide")
    st.title("Trusted Financial Sources")

    st.write("These are reputable sites across financial news, investment firms, research, and policy.")

    # === Trusted Sources with Logos ===
    financial_news = {
        "Bloomberg": ("https://www.bloomberg.com", "https://logo.clearbit.com/bloomberg.com"),
        "WSJ": ("https://www.wsj.com", "https://logo.clearbit.com/wsj.com"),
        "CNBC": ("https://www.cnbc.com", "https://logo.clearbit.com/cnbc.com"),
        "Reuters": ("https://www.reuters.com", "https://logo.clearbit.com/reuters.com"),
        "MarketWatch": ("https://www.marketwatch.com", "https://logo.clearbit.com/marketwatch.com"),
        "Yahoo Finance": ("https://finance.yahoo.com", "https://logo.clearbit.com/yahoo.com"),
    }

    st.subheader("Financial News")
    render_cards(financial_news)

# === Function to render in columns ===
def render_cards(link_dict, cols_per_row=3):
    keys = list(link_dict.keys())
    for i in range(0, len(keys), cols_per_row):
        row = keys[i:i + cols_per_row]
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            url, logo = link_dict[name]
            with col:
                st.image(logo, width=32)
                st.markdown(f"[**{name}**]({url})")

