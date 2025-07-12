import streamlit as st

def run():
    st.set_page_config(page_title="Test", layout="wide")
    st.title("Trusted Financial Sources")
    st.write("✅ If you can see this, the page is working.")

    # Minimal test grid (no CSS, no logos)
    links = {
        "Bloomberg": "https://www.bloomberg.com",
        "WSJ": "https://www.wsj.com",
        "CNBC": "https://www.cnbc.com",
    }

    cols = st.columns(len(links))
    for col, (name, url) in zip(cols, links.items()):
        col.markdown(f"[**{name}**]({url})")
