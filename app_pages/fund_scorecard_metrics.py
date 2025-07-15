import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches
import together

# ✅ Use your existing secrets structure
together.api_key = st.secrets["together"]["api_key"]

# --- Build Fund‑Name ➜ Ticker lookup ---
def build_ticker_lookup(pdf):
    lookup = {}
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.split("\n"):
            parts = line.strip().rsplit(" ", 1)
            if len(parts) == 2:
                fund, ticker = parts
                if re.match(r"^[A-Z]{4,6}$", ticker.strip()):
                    lookup[fund.strip()] = ticker.strip()
    return lookup

# --- Together fallback to identify fund name ---
def identify_fund_with_llm(block, lookup_keys):
    prompt = f"""
You are analyzing a fund performance summary. Given this block:

\"\"\"{block}\"\"\"

And this list of known fund names:

{lookup_keys}

Which fund is this block referring to? Respond with the exact name from the list, or say "UNKNOWN".
"""
    try:
        response = together.Complete.create(
            prompt=prompt,
            model="mistral-7b-instruct",
            max_tokens=50,
            temperature=0.3,
            stop=["\n"]
        )
        result = response["output"]["choices"][0]["text"].strip()
        return result if result in lookup_keys else "UNKNOWN FUND"
    except Exception as e:
        st.warning(f"LLM fallback failed: {e}")
        return "UNKNOWN FUND"

# --- Get fund name from block using multiple methods ---
def get_fund_name(block, lookup):
    block_lower = block.lower()
    for name in lookup:
        if name.lower() in block_lower:
            return name

    lines = block.split("\n")[:6]
    candidates = [line.strip() for line in lines if sum(c.isupper() for c in line) > 5]

    for line in candidates:
        matches = get_close_matches(line, lookup.keys(), n=1, cutoff=0.6)
        if matches:
            return matches[0]

    # Final fallback: Together AI
    return identify_fund_with_llm(block, list(lookup.keys()))

# --- Streamlit App ---
def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    pdf_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if pdf_file:
        rows = []
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            status_text = st.empty()
            progress = st.progress(0)

            ticker_lookup = build_ticker_lookup(pdf)

            for i, page in enumerate(pdf.pages):
                txt = page.extract_text()
                if not txt:
                    progress.progress((i + 1) / total_pages)
                    status_text.text(f"Skipping page {i + 1} (no text)...")
                    continue

                blocks = re.split(
                    r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))",
                    txt)

                for block in blocks:
                    if not block.strip():
                        continue

                    fund_name = get_fund_name(block, ticker_lookup)
                    ticker = ticker_lookup.get(fund_name, "N/A")
                    meets = "Yes" if "placed on watchlist" not in block else "No"

                    metrics = {}
                    for line in block.split("\n"):
                        if line.startswith((
                            "Manager Tenure", "Excess Performance", "Peer Return Rank",
                            "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
                            "Sortino Ratio Rank", "Tracking Error Rank")):
                            m = re.match(r"^(.*?)\s+(Pass|Review)", line.strip())
                            if m:
                                metrics[m.group(1).strip()] = m.group(2).strip()

                    if metrics:
                        rows.append({
                            "Fund Name": fund_name,
                            "Ticker": ticker,
                            "Meets Criteria": meets,
                            **metrics
                        })

                progress.progress((i + 1) / total_pages)
                status_text.text(f"Processed page {i + 1} of {total_pages}")

            progress.empty()
            status_text.empty()

        if rows:
            df = pd.DataFrame(rows)
            st.success(f"✅ Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download as CSV",
                                   data=csv,
                                   file_name="fund_criteria_results.csv",
                                   mime="text/csv")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
