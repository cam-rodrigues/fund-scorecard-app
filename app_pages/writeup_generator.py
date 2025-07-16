import streamlit as st
import pdfplumber
import re
from jinja2 import Template

st.set_page_config(page_title="Fund Writeup Generator", layout="wide")
st.title("📄 Fund Writeup Generator")

st.markdown("Upload an MPI-style fund scorecard to auto-generate a summary writeup.")


# --- PDF Text Extractor ---
def extract_pdf_text(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])


# --- Example Metrics Extractor (very rough) ---
def extract_sample_metrics(text, fund_name):
    # Search for line with fund name followed by 5 return figures
    pattern = rf"{re.escape(fund_name)}.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%.*?(-?\d+\.\d+)%"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return {
            "qtd": match.group(1),
            "1yr": match.group(2),
            "3yr": match.group(3),
            "5yr": match.group(4),
            "10yr": match.group(5)
        }
    return {
        "qtd": "N/A",
        "1yr": "N/A",
        "3yr": "N/A",
        "5yr": "N/A",
        "10yr": "N/A"
    }


# --- Writeup Generator ---
def generate_writeup(fund_name, manager, peer_rank, rec, metrics):
    template = Template("""
### {{ fund_name }}

**Performance Summary**
- QTD: {{ metrics.qtd }}%
- 1YR: {{ metrics.1yr }}%
- 3YR: {{ metrics.3yr }}%
- 5YR: {{ metrics.5yr }}%
- 10YR: {{ metrics.10yr }}%

**Manager & Strategy**
Managed by **{{ manager }}**, this fund has demonstrated performance {{ peer_rank }} compared to its peers.

**Recommendation**
**Action:** {{ rec }}
""")
    return template.render(fund_name=fund_name, metrics=metrics, manager=manager, peer_rank=peer_rank, rec=rec)


# === Streamlit Upload + Form ===
uploaded = st.file_uploader("Upload MPI PDF", type=["pdf"])
if uploaded:
    text = extract_pdf_text(uploaded)

    fund_name = st.text_input("Fund Name", value="BlackRock Mid Cap Growth Equity")
    manager = st.text_input("Manager Name", value="Phil Ruvinsky")
    peer_rank = st.selectbox("Peer Rank", ["Top Quartile", "Middle Quartile", "Bottom Quartile"])
    rec = st.selectbox("Action", ["Recommended", "Watchlist", "Replace", "Hold"])

    metrics = extract_sample_metrics(text, fund_name)

    if st.button("Generate Writeup"):
        writeup = generate_writeup(fund_name, manager, peer_rank, rec, metrics)
        st.markdown(writeup)
