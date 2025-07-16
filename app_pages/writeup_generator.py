import streamlit as st
import pdfplumber
import re
import textwrap
from jinja2 import Template

# === Main App Function ===
def run():
    st.set_page_config(page_title="Fund Writeup Generator", layout="wide")
    st.title("📄 Fund Writeup Generator")

    st.markdown("Upload an MPI-style PDF and generate a client-ready writeup.")

    # === Step 1: Upload PDF ===
    uploaded_file = st.file_uploader("Upload MPI-style PDF", type=["pdf"])

    if uploaded_file:
        pdf_text = extract_pdf_text(uploaded_file)

        # === Step 2: Input Form ===
        with st.form("writeup_form"):
            fund_name = st.text_input("Fund Name", value="BlackRock Mid Cap Growth Equity")
            manager = st.text_input("Manager Name", value="Phil Ruvinsky")
            peer_rank = st.selectbox("Peer Rank", ["Top Quartile", "Middle Quartile", "Bottom Quartile"])
            rec = st.selectbox("Recommendation", ["Recommended", "Watchlist", "Replace", "Hold"])
            submit = st.form_submit_button("Generate Writeup")

        if submit:
            metrics = extract_sample_metrics(pdf_text, fund_name)
            writeup = generate_writeup(fund_name, manager, peer_rank, rec, metrics)

            st.markdown("---")
            st.subheader("📋 Writeup Preview")
            st.markdown(writeup)


# === Extract full text from uploaded PDF ===
def extract_pdf_text(file_obj):
    with pdfplumber.open(file_obj) as pdf:
        return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])


# === Find return metrics near the fund name line ===
def extract_sample_metrics(text, fund_name):
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
    return {k: "N/A" for k in ["qtd", "1yr", "3yr", "5yr", "10yr"]}


# === Generate writeup using Jinja2 ===
def generate_writeup(fund_name, manager, peer_rank, rec, metrics):
    template_str = textwrap.dedent("""
        ### {{ fund_name }}

        **Performance Summary**
        - QTD: {{ metrics["qtd"] }}%
        - 1YR: {{ metrics["1yr"] }}%
        - 3YR: {{ metrics["3yr"] }}%
        - 5YR: {{ metrics["5yr"] }}%
        - 10YR: {{ metrics["10yr"] }}%

        **Manager & Strategy**
        Managed by **{{ manager }}**, this fund has demonstrated performance {{ peer_rank }} relative to its peers.

        **Recommendation**
        **Action:** {{ rec }}
    """)

    template = Template(template_str)
    return template.render(
        fund_name=fund_name,
        metrics=metrics,
        manager=manager,
        peer_rank=peer_rank,
        rec=rec
    )
