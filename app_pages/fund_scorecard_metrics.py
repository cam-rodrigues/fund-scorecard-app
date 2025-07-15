import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches
import together

together.api_key = st.secrets["together"]["api_key"]

# --- Build Fund Name ➜ Ticker lookup ---
def build_ticker_lookup(pdf):
    lookup = {}
    for page in pdf.pages:
        lines = page.extract_text().split("\n") if page.extract_text() else []

        for i in range(len(lines) - 1):
            name = lines[i].strip()
            maybe_ticker = lines[i + 1].strip()
            if re.match(r"^[A-Z]{4,6}X?$", maybe_ticker) and len(name.split()) > 1:
                lookup[name] = maybe_ticker

        for line in lines:
            parts = line.strip().rsplit(" ", 1)
            if len(parts) == 2 and re.match(r"^[A-Z]{4,6}X?$", parts[1]):
                lookup[parts[0].strip()] = parts[1].strip()
    return lookup

# --- Get fund name from block (smart fallback) ---
def get_fund_name(block, lookup):
    block_lower = block.lower()

    # ✅ Try exact match first
    for name in lookup:
        if name.lower() in block_lower:
            return name

    lines = [line.strip() for line in block.split("\n") if line.strip()]
    name_candidates = []

    # 🚫 Ignore lines that are clearly not fund names
    skip_patterns = [
        re.compile(r"fund meets", re.IGNORECASE),
        re.compile(r"watchlist", re.IGNORECASE),
        re.compile(r"\b(as of|[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})\b", re.IGNORECASE)
    ]

    for line in lines:
        if any(p.search(line) for p in skip_patterns):
            continue
        if sum(c.isupper() for c in line) > 5 and 3 <= len(line.split()) <= 12:
            name_candidates.append(line)

    for candidate in name_candidates:
        if candidate in lookup:
            return candidate
        match = get_close_matches(candidate, lookup.keys(), n=1, cutoff=0.5)
        if match:
            return match[0]

    return "UNKNOWN FUND"

# --- Optional LLM fallback ---
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
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            max_tokens=50,
            temperature=0.3,
            stop=["\n"]
        )
        result = response["choices"][0]["text"].strip()
        return result if result in lookup_keys else "UNKNOWN FUND"
    except Exception as e:
        st.warning(f"LLM fallback failed: {e}")
        return "UNKNOWN FUND"

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
        original_blocks = []
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
                    r"\n(?=[^\n]*?(Fund )?(Meets Watchlist Criteria|has been placed on watchlist))",
                    txt)

                for block in blocks:
                    if not block.strip():
                        continue

                    fund_name = get_fund_name(block, ticker_lookup)

                    # ✅ Match or fuzzy-match ticker
                    if fund_name in ticker_lookup:
                        ticker = ticker_lookup[fund_name]
                    else:
                        match = get_close_matches(fund_name, ticker_lookup.keys(), n=1, cutoff=0.5)
                        ticker = ticker_lookup[match[0]] if match else "N/A"

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
                        original_blocks.append(block)

                progress.progress((i + 1) / total_pages)
                status_text.text(f"Processed page {i + 1} of {total_pages}")

            progress.empty()
            status_text.empty()

        # 🔁 Final LLM fallback for UNKNOWN rows
        df = pd.DataFrame(rows)
        for i, row in df.iterrows():
            if row["Fund Name"] == "UNKNOWN FUND" or row["Ticker"] == "N/A":
                block = original_blocks[i]
                llm_name = identify_fund_with_llm(block, list(ticker_lookup.keys()))
                if llm_name != "UNKNOWN FUND":
                    df.at[i, "Fund Name"] = llm_name
                    df.at[i, "Ticker"] = ticker_lookup.get(llm_name, "N/A")

        if not df.empty:
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
