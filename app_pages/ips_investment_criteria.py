import streamlit as st
import pdfplumber
import re
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Step 13: Extract Performance Info", layout="wide")
    st.title("Step 13: Fund Performance - Ticker, Category, Benchmark")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step13_final")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === TOC parsing ===
            toc_text = pdf.pages[1].extract_text()
            def get_page(section_title):
                for line in toc_text.split("\n"):
                    if section_title in line:
                        m = re.search(r"(\d+)$", line)
                        return int(m.group(1)) if m else None
                return None

            scorecard_page = get_page("Fund Scorecard")
            perf_page = get_page("Fund Performance: Current vs. Proposed Comparison")
            if not scorecard_page or not perf_page:
                st.error("❌ Could not find required TOC entries.")
                return

            # === Fund Names from Scorecard ===
            scorecard_lines = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text or "Style Box Analysis" in text:
                    break
                scorecard_lines.extend(text.split("\n"))

            fund_names = []
            i = 0
            while i < len(scorecard_lines):
                if "Manager Tenure" in scorecard_lines[i]:
                    if i > 0:
                        name = scorecard_lines[i - 1].strip()
                        name = re.sub(r"Fund Meets Watchlist Criteria\.", "", name)
                        name = re.sub(r"Fund has been placed on watchlist.*", "", name).strip()

                        if (
                            name
                            and "criteria threshold" not in name.lower()
                            and "style" not in name.lower()
                            and "asset loading" not in name.lower()
                            and not name.lower().startswith("fund facts")
                        ):
                            fund_names.append(name)
                    i += 14
                else:
                    i += 1

            def short_key(name):
                return " ".join(name.split()[:5])
            short_keys = {short_key(name): name for name in fund_names}

            # === Extract all lines from performance section ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if not text or "Fund Factsheets" in text:
                    break
                perf_lines.extend(text.split("\n"))
            all_perf_lines = [line.strip() for line in perf_lines if len(line.strip()) > 5]

            fund_perf_data = {}

            for key, full_name in short_keys.items():
                match = get_close_matches(key, all_perf_lines, n=1, cutoff=0.7)
                if not match:
                    fund_perf_data[full_name] = {
                        "match_found": False,
                        "ticker": "Not Found",
                        "category": "Unknown",
                        "benchmark": "Unknown"
                    }
                    continue

                matched_line = match[0]
                idx = perf_lines.index(matched_line)

                # === Ticker: 5-letter uppercase, anywhere in the line ===
                ticker_match = re.findall(r"\b[A-Z]{5}\b", matched_line)
                ticker = ticker_match[0] if ticker_match else "Not Found"

                # === Category: Go up until we find a line with no digits ===
                category = "Unknown"
                for j in range(idx - 1, -1, -1):
                    line_above = perf_lines[j].strip()
                    if not any(char.isdigit() for char in line_above):
                        category = line_above
                        break

                # === Benchmark: line after the match ===
                benchmark = perf_lines[idx + 1].strip() if idx + 1 < len(perf_lines) else "Unknown"

                fund_perf_data[full_name] = {
                    "match_found": True,
                    "ticker": ticker,
                    "category": category,
                    "benchmark": benchmark,
                    "match_line": matched_line
                }

            # === Display Results ===
            st.subheader("Fund Performance Info")
            for fund in fund_names:
                info = fund_perf_data.get(fund, {})
                st.markdown(f"### {'✅' if info.get('match_found') else '❌'} {fund}")
                st.markdown(f"- **Ticker:** {info.get('ticker', 'Not Found')}")
                st.markdown(f"- **Category:** {info.get('category', 'Unknown')}")
                st.markdown(f"- **Benchmark:** {info.get('benchmark', 'Unknown')}")
                if info.get("match_found"):
                    st.markdown(f"- Matched Line: `{info['match_line']}`")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
