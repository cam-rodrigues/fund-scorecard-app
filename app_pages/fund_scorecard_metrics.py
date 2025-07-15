# fund_scorecard_metrics.py
import io
import re
import tempfile
from pathlib import Path

import pandas as pd
import pdfplumber
import streamlit as st

# ────────────────────────────────
# 1. Regex helpers
# ────────────────────────────────
TICKER_RE = re.compile(r"(.+?)\s{2,}([A-Z0-9]{1,6}[A-Z]?)\s?[†*]?$")
METRIC_RE = re.compile(
    r"^(Manager Tenure|Excess Performance|Peer Return Rank|Expense Ratio Rank|"
    r"Sharpe Ratio Rank|R-Squared|Sortino Ratio Rank|Tracking Error Rank)"
    r"\s+(Pass|Review)"
)

WATCHLIST_POS = re.compile(r"Fund Meets Watchlist Criteria", flags=re.I)
WATCHLIST_NEG = re.compile(r"placed on watchlist", flags=re.I)

# ────────────────────────────────
# 2. Build master lookup  (Fund ➜ Ticker)
# ────────────────────────────────
def build_ticker_lookup(pages_text: list[str]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for page_txt in pages_text:
        for line in page_txt.splitlines():
            m = TICKER_RE.match(line.strip())
            if m:
                lookup[m.group(1).strip()] = m.group(2).strip()
    return lookup


# ────────────────────────────────
# 3. Find best‑matching fund name in a block
# ────────────────────────────────
def pick_fund_name(block: str, lookup: dict[str, str]) -> tuple[str, bool]:
    """Return (fund_name, confident?)."""
    block_lower = block.lower()

    # 3‑A. Exact substring first
    for name in lookup:
        if name.lower() in block_lower:
            return name, True

    # 3‑B. Fuzzy match (RapidFuzz ≥85)
    try:
        from rapidfuzz import fuzz, process  # type: ignore
    except ModuleNotFoundError:
        return "UNKNOWN FUND", False

    choice, score, _ = process.extractOne(
        block, lookup.keys(), scorer=fuzz.token_set_ratio  # type: ignore
    )
    return (choice, score >= 85)


# ────────────────────────────────
# 4. Main Streamlit app
# ────────────────────────────────
def run():
    st.set_page_config("Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown(
        "Upload an **MPI‑style PDF** fund scorecard. The app extracts each fund, "
        "evaluates it against the watch‑list criteria, and shows a breakdown of "
        "metric statuses."
    )

    pdf_bytes = st.file_uploader("📄 Upload MPI PDF", type=["pdf"])
    if not pdf_bytes:
        st.info("Waiting for a PDF…")
        st.stop()

    # Save to a temp file so pdfplumber can memory‑map large docs safely
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes.read())
        tmp_path = Path(tmp.name)

    rows: list[dict] = []
    low_confidence: list[dict] = []

    # ── Pass 1: read every page txt once ──
    pages_text: list[str] = []
    with pdfplumber.open(tmp_path) as pdf:
        progress = st.progress(0.0, "🔍 Scanning PDF…")
        for i, page in enumerate(pdf.pages, start=1):
            pages_text.append(page.extract_text() or "")
            progress.progress(i / len(pdf.pages))
        progress.empty()

    ticker_lookup = build_ticker_lookup(pages_text)

    # ── Pass 2: parse criteria blocks ──
    st.caption("Parsing watch‑list sections…")
    block_splitter = re.compile(
        r"\n(?=[^\n]{0,120}Fund (?:Meets Watchlist Criteria|has been placed on watchlist))",
        flags=re.I,
    )

    for page_txt in pages_text:
        if "Fund Scorecard" not in page_txt:
            continue
        # If horizontal rule markers exist (“────────”), split on them too
        sections = re.split(r"(?:─{5,})", page_txt)
        for section in sections:
            blocks = block_splitter.split(section)
            for block in blocks:
                if not WATCHLIST_POS.search(block) and not WATCHLIST_NEG.search(block):
                    continue

                name, confident = pick_fund_name(block, ticker_lookup)
                ticker = ticker_lookup.get(name, "N/A")
                meets = "Yes" if WATCHLIST_NEG.search(block) is None else "No"

                metrics = {
                    m.group(1): m.group(2)
                    for m in (METRIC_RE.match(line.strip()) for line in block.splitlines())
                    if m
                }

                record = {
                    "Fund Name": name,
                    "Ticker": ticker,
                    "Meets Criteria": meets,
                    **metrics,
                }

                if confident:
                    rows.append(record)
                else:
                    low_confidence.append(record)

    # ── Output results ──
    if not rows and not low_confidence:
        st.error("❌ No fund entries found. This PDF may use an unsupported template.")
        st.stop()

    df = pd.DataFrame(rows)
    st.success(f"✅ Captured {len(df)} fund entries.")
    st.dataframe(df, use_container_width=True)

    if low_confidence:
        st.warning(
            f"⚠️ {len(low_confidence)} additional entries had low‑confidence name matches."
        )
        with st.expander("Show low‑confidence matches"):
            st.dataframe(pd.DataFrame(low_confidence), use_container_width=True)

    # Downloads
    with st.expander("📥 Download Results"):
        st.download_button(
            "CSV (high‑confidence only)",
            df.to_csv(index=False).encode(),
            file_name="fund_criteria_results.csv",
            mime="text/csv",
        )
        if low_confidence:
            all_df = pd.concat([df, pd.DataFrame(low_confidence)], ignore_index=True)
            st.download_button(
                "CSV (all entries)",
                all_df.to_csv(index=False).encode(),
                file_name="fund_criteria_results_all.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    run()
