import streamlit as st
import pdfplumber
import re

def run():
    st.set_page_config(page_title="Step 13: Fund Performance Extract", layout="wide")
    st.title("Step 13: Extract Fund Performance Info")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step13_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Step 1: Fund Names from Scorecard Section (re-run block from Step 12) ===
            def get_scorecard_page(toc_text):
                for line in toc_text.split("\n"):
                    if "Fund Scorecard" in line:
                        m = re.search(r"(\d+)$", line)
                        return int(m.group(1)) if m else None
                return None

            def get_perf_page(toc_text):
                for line in toc_text.split("\n"):
                    if "Fund Performance: Current vs. Proposed Comparison" in line:
                        m = re.search(r"(\d+)$", line)
                        return int(m.group(1)) if m else None
                return None

            # --- TOC
            toc_text = pdf.pages[1].extract_text()
            scorecard_page = get_scorecard_page(toc_text)
            perf_page = get_perf_page(toc_text)

            if not scorecard_page or not perf_page:
                st.error("❌ Could not find required TOC sections.")
                return

            # === Step 2: Extract Cleaned Fund Names from Scorecard Section ===
            scorecard_lines = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if text and "Fund Scorecard" in text:
                    scorecard_lines.extend(text.split("\n"))
                else:
                    break  # exit if we move past scorecard section

            # --- Remove boilerplate
            skip_keywords = ["Criteria Threshold", "must outperform", "Created with mpi Stylus"]
            scorecard_lines = [l.strip() for l in scorecard_lines if not any(k in l for k in skip_keywords)]

            # --- Extract names above "Manager Tenure"
            fund_names = []
            i = 0
            while i < len(scorecard_lines):
                if "Manager Tenure" in scorecard_lines[i]:
                    if i > 0:
                        fund_name = scorecard_lines[i - 1]
                        fund_name = re.sub(r"Fund Meets Watchlist Criteria\.", "", fund_name)
                        fund_name = re.sub(r"Fund has been placed on watchlist.*", "", fund_name).strip()
                        if fund_name and "FUND FACTS 3 YEAR ROLLING STYLE" not in fund_name.upper():
                            fund_names.append(fund_name)
                    i += 14
                else:
                    i += 1

            # === Step 3: Extract Tickers, Categories, Benchmarks ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if text and "Fund Performance: Current vs. Proposed Comparison" in text:
                    perf_lines.extend(text.split("\n"))
                else:
                    break  # exit if we move past section

            # Create map: fund_name ➝ (ticker, category, benchmark)
            fund_perf_data = {}

            for i, line in enumerate(perf_lines):
                for fund in fund_names:
                    if fund in line:
                        # Check right side of line for 5-letter uppercase ticker
                        right_part = line.split(fund)[-1]
                        match = re.search(r"\b([A-Z]{5})\b", right_part)
                        ticker = match.group(1) if match else "Not Found"

                        # Category = line above
                        category = perf_lines[i - 1].strip() if i > 0 else "Unknown"

                        # Benchmark = line below
                        benchmark = perf_lines[i + 1].strip() if i + 1 < len(perf_lines) else "Unknown"

                        fund_perf_data[fund] = {
                            "ticker": ticker,
                            "category": category,
                            "benchmark": benchmark
                        }

            # === Step 4: Display Results ===
            st.subheader("Fund Performance Extracted Info")
            for fund in fund_names:
                data = fund_perf_data.get(fund, {})
                ticker = data.get("ticker", "Not Found")
                category = data.get("category", "Unknown")
                benchmark = data.get("benchmark", "Unknown")

                st.markdown(f"### {fund}")
                st.markdown(f"- **Ticker:** {ticker}")
                st.markdown(f"- **Category:** {category}")
                st.markdown(f"- **Benchmark:** {benchmark}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
