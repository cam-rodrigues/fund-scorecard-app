import streamlit as st
import requests

# === CONFIG: Curated List of Trusted Domains ===
TRUSTED_DOMAINS = [
    # Tier 1 Financial News & Data
    "bloomberg.com", "wsj.com", "reuters.com", "ft.com", "cnbc.com", "marketwatch.com",
    "morningstar.com", "fool.com", "investopedia.com", "seekingalpha.com", "yahoo.com",

    # Investment Firms & Institutional Insights
    "blackrock.com", "vanguard.com", "fidelity.com", "schwab.com", "jpmorgan.com",
    "goldmansachs.com", "morganstanley.com", "alliancebernstein.com", "bain.com", "mckinsey.com",

    # Academic & Research Institutions
    "cfainstitute.org", "harvard.edu", "mit.edu", "wharton.upenn.edu", "yale.edu",
    "chicagobooth.edu", "mba.tuck.dartmouth.edu", "nber.org",

    # Government & Policy Sources
    "sec.gov", "federalreserve.gov", "treasury.gov", "imf.org", "worldbank.org", "oecd.org",

    # General Reputable News
    "nytimes.com", "npr.org", "forbes.com", "cnn.com", "economist.com"
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
st.set_page_config(page_title="Reputable Source Finder", layout="wide")
st.title("Reputable Financial Source Finder")

st.markdown("Use this tool to discover **high-quality financial or economic sources** for any topic. It filters Google search results by trusted domains.")

query = st.text_input("Enter a topic (e.g. '401k rollover fees', 'impact of interest rates on bonds'):")
api_key = st.text_input("Enter your SerpAPI key:", type="password")

if st.button("Search") and query and api_key:
    with st.spinner("Searching reputable sources..."):
        sources = fetch_reputable_sources(query, api_key)

    if sources:
        st.success(f"Found {len(sources)} reputable sources:")
        for s in sources:
            st.markdown(f"**[{s['title']}]({s['link']})**\n\n{s['snippet']}\n")
    else:
        st.warning("No reputable sources found. Try refining your query.")
