import streamlit as st
import pdfplumber
import re
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Step 13: Fuzzy Fund Performance Match", layout="wide")
    st.title("Step 13: Extract Fund Performance Info with Matching")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step13_fuzzy")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Get TOC and Page Numbers ===
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

            # === Extract Fund Names from Scorecard Section ===
            scorecard_lines = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if text and "Fund Scorecard" in text:
                    scorecard_lines.extend(text.split("\n"))
                else:
                    break

            fund_names = []
            i = 0
            while i < len(scorecard_lines):
                if "Manager Tenure" in scorecard_lines[i]:
                    if i > 0:
                        raw_name = scorecard_lines[i - 1]
                        name = re.sub(r"Fund Meets Watchlist Criteria\.", "", raw_name)
                        name = re.sub(r"Fund has been placed on watchlist.*", "", name).strip()
                        if name and "FUND FACTS 3 YEAR ROLLING STYLE" not in name.upper():
                            fund_names.append(name)
                    i += 14
                else:
                    i += 1

            # === Extract Text from Performance Section ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if text and "Fund Performance: Current vs. Proposed Comparison" in text:
                    perf_lines.extend(text.split("\n"))
                else:
                    break

            # === Fuzzy Match Each Fund Name ===
            fund_perf_data = {}
            all_perf_lines = [line.strip() for line in perf_lines if len(line.strip()) > 10]
            for fund in fund_names:
                match = get_close_matches(fund, all_perf_lines, n=1, cutoff=0.7)
                if not match:
                    fund_perf_data[fund] = {
                        "match_found": False,
                        "ticker": "Not Found",
                        "category": "Unknown",
                        "benchmark": "Unknown"
                    }
                    continue

                matched_line = match[0]
                idx = perf_lines.index(matched_line)
                right_part = matched_line.split(fund)[-1]
                ticker_match = re.search(r"\b([A-Z]{5})\b", right_part)
                ticker = ticker_match.group(1) if ticker_match else "Not Found"
                category = perf_lines[idx - 1].strip() if idx > 0 else "Unknown"
                benchmark = perf_lines[idx + 1].strip() if idx + 1 < len(perf_lines) else "Unknown"

                fund_perf_data[fund] = {
                    "match_found": True,
                    "match_line": matched_line,
                    "ticker": ticker,
                    "category": category,
                    "benchmark": benchmark
                }

            # === Display Results ===
            st.subheader("Fund Performance Info (Fuzzy Matched)")
            for fund in fund_names:
                info = fund_perf_data.get(fund, {})
                if not info.get("match_found"):
                    st.markdown(f"### ❌ {fund}")
                    st.markdown(f"- Ticker: Not Found")
                    st.markdown(f"- Category: Unknown")
                    st.markdown(f"- Benchmark: Unknown")
                    st.markdown("---")
                    continue

                st.markdown(f"### ✅ {fund}")
                st.markdown(f"- **Matched Line:** {info['match_line']}")
                st.markdown(f"- **Ticker:** {info['ticker']}")
                st.markdown(f"- **Category:** {info['category']}")
                st.markdown(f"- **Benchmark:** {info['benchmark']}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error: {e}")
