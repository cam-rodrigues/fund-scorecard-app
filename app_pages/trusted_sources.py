import streamlit as st
import requests

# === CONFIG ===
TRUSTED_DOMAINS = [
    "forbes.com", "bloomberg.com", "wsj.com", "reuters.com", "nytimes.com", "cnn.com",
    "npr.org", "nature.com", "sciencedirect.com", "harvard.edu", "stanford.edu"
]

def fetch_reputable_sources(query, api_key):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": "20"
    }
    res = requests.get(url, params=params)
    results = res.json().get("organic_results", [])

    reputable = []
    for result in results:
        link = result.get("link", "")
        source = link.split("/")[2] if "://" in link else ""
        if any(domain in source for domain in TRUSTED_DOMAINS):
            reputable.append({
                "title": result.get("title", ""),
                "link": link,
                "snippet": result.get("snippet", "")
            })

    return reputable

# === Streamlit UI ===
st.title("Reputable Source Finder")

query = st.text_input("Enter a topic to research:")
api_key = st.text_input("Enter your SerpAPI key:", type="password")

if st.button("Search") and query and api_key:
    with st.spinner("Searching reputable sources..."):
        sources = fetch_reputable_sources(query, api_key)

    if sources:
        st.success(f"Found {len(sources)} reputable sources:")
        for s in sources:
            st.markdown(f"**[{s['title']}]({s['link']})**\n\n{s['snippet']}\n")
    else:
        st.warning("No reputable sources found.")
