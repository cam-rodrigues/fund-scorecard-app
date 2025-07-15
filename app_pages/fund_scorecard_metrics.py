import streamlit as st
import pdfplumber
import pandas as pd
import re
from difflib import get_close_matches
from io import BytesIO

# --- Ticker Lookup (stacked + inline formats) ---
def build_ticker_lookup(pdf):
    lookup = {}

    for page in pdf.pages:
        lines = page.extract_text().split("\n") if page.extract_text() else []

        for i in range(len(lines) - 1):
            name_line = lines[i].strip()
            ticker_line = lines[i + 1].strip()

            if (
                re.match(r"^[A-Z]{4,6}X?$", ticker_line)
                and len(name_line.split()) >= 3
                and not re.match(r"^[A-Z]{4,6}X?$", name_line)
            ):
                clean_name = " ".join(name_line.split())
                lookup[clean_name] = ticker_line.strip()

        for line in lines:
            line = line.strip()
            parts = line.rsplit(" ", 1)
            if (
                len(parts) == 2
                and re.match(r"^[A-Z]{4,6}X?$", parts[1])
                and len(parts[0].split()) >= 3
            ):
                lookup[parts[0].strip()] = parts[1].strip()

    return lookup

# --- Extract fund name from block ---
def get_fund_name(block, lookup):
    block_lower = block.lower()
    for name in lookup:
        if name.lower() in block_lower:
            return name

    lines = block.split("\n")
    top_lines = lines[:6]
    candidates = [line.strip() for line in top_lines if sum(c.isupper() for c in line) > 5]

    for line in candidates:
        matches = get_close_matches(line, lookup.keys(), n=1, cutoff=0.5)
        if matches:
            return matches[0]

    metric_start = None
    for i, line in enumerate(lines):
        if any(metric in line for metric in [
            "Manager Tenure", "Excess Performance", "Peer Return Rank",
            "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
            "Sortino Ratio Rank", "Tracking Error Rank"
        ]):
            metric_start = i
            break

    if metric_start and metric_start > 0:
        fallback_name = lines[metric_start - 1].strip()
        fallback_name = re.sub(r"(This|The)?\s?fund\s(has|meets).*", "", fallback_name, flags=re.IGNORECASE).strip()
        if fallback_name:
            return fallback_name

    return "UNKNOWN FUND"

# --- Main App ---
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

            # ✅ Manual patch for known missing WisdomTree fund
            if not any("Enhanced Commodity" in name for name in ticker_lookup):
                ticker_lookup["WisdomTree Enhanced Commodity Stgy Fd"] = "WTES"

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
                    ticker = ticker_lookup.get(fund_name, "N/A")
                    meets = "Yes" if "placed on watchlist" not in block else "No"

                    metrics = {}
                    for line in block.split("\n"):
                        if line.startswith((
                            "Manager Tenure", "Excess Performance", "Peer Return Rank",
                            "Expense Ratio Rank", "Sharpe Ratio Rank", "R-Squared",
                            "Sortino Ratio Rank", "Tracking Error Rank", "Tracking Error (3Yr)", "Tracking Error (5Yr)".)):
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

        df = pd.DataFrame(rows)

        # Final ticker correction (fuzzy + substring)
        for i, row in df.iterrows():
            if row["Ticker"] == "N/A" and row["Fund Name"] != "UNKNOWN FUND":
                fund_name = row["Fund Name"]
                match = get_close_matches(fund_name, ticker_lookup.keys(), n=1, cutoff=0.5)
                if match:
                    df.at[i, "Ticker"] = ticker_lookup[match[0]]
                else:
                    for known_name in ticker_lookup:
                        if fund_name.lower() in known_name.lower() or known_name.lower() in fund_name.lower():
                            df.at[i, "Ticker"] = ticker_lookup[known_name]
                            break

        if not df.empty:
            st.success(f"Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                # CSV export
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download as CSV",
                                   data=csv,
                                   file_name="fund_criteria_results.csv",
                                   mime="text/csv")

                # Excel export
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Fund Criteria")
                excel_data = output.getvalue()

                st.download_button("Download as Excel",
                                   data=excel_data,
                                   file_name="fund_criteria_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
