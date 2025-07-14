import streamlit as st
import pdfplumber
import pandas as pd
import re

def normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())

def simple_similarity(a, b):
    a, b = normalize_name(a), normalize_name(b)
    matches = sum((char in b) for char in a)
    return matches / max(len(a), len(b))

def run():
    st.set_page_config(page_title="Fund Scorecard Metrics", layout="wide")
    st.title("Fund Scorecard Metrics")

    st.markdown("""
    Upload an MPI-style PDF fund scorecard below. The app will extract each fund, determine if it meets the watchlist criteria, and display a detailed breakdown of metric statuses.
    """)

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Processing PDF..."):
            fund_meta = {}
            criteria_data = []
            metadata_index = []

            fund_type_phrases = [
                "Large Cap Growth", "Large Cap Value", "Large Blend",
                "Mid Cap Growth", "Mid Cap Value", "Mid Cap Blend",
                "Small Cap Growth", "Small Cap Value", "Small Blend",
                "Target-Date Retirement", "Target-Date 2025", "Target-Date 2030",
                "Target-Date 2040", "Target-Date 2045", "Target-Date 2050",
                "Target-Date 2055", "Target-Date 2060", "Target-Date 2065",
                "Intermediate Core Bond", "Intermediate Core-Plus Bond",
                "Inflation-Protected Bond", "Multisector Bond", "Global Bond",
                "Commodities Broad Basket", "Real Estate", "International",
                "Emerging Markets", "Equity", "Fixed Income", "Stock", "Bond"
            ]

            share_class_keywords = ["Admiral", "Instl", "Institutional", "R6", "Z", "I", "K", "N"]

            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)

                # === Phase 1: Build fund metadata from performance pages (first 15) ===
                for i in range(min(15, total_pages)):
                    lines = pdf.pages[i].extract_text().split("\n")
                    for j, line in enumerate(lines):
                        ticker_match = re.match(r"^(.*?)([A-Z]{4,6})$", line.strip())
                        if ticker_match and j + 1 < len(lines):
                            fund_name = ticker_match.group(1).strip()
                            ticker = ticker_match.group(2).strip()
                            style_box_line = lines[j + 1].strip()
                            fund_type = next((ftype for ftype in fund_type_phrases if ftype.lower() in style_box_line.lower()), "N/A")
                            share_class = next((w for w in fund_name.split() if w in share_class_keywords), "N/A")

                            norm_name = normalize_name(fund_name)
                            fund_meta[norm_name] = {
                                "Fund Name": fund_name,
                                "Ticker": ticker,
                                "Style Box": style_box_line if style_box_line else "N/A",
                                "Fund Type": fund_type,
                                "Share Class": share_class
                            }

                # === Phase 2: Build metadata index from full document ===
                for i in range(total_pages):
                    lines = pdf.pages[i].extract_text().split("\n")
                    for j, line in enumerate(lines):
                        if "Manager:" in line or "Inception Date:" in line or "Benchmark:" in line:
                            entry = {"Manager": "N/A", "Inception Date": "N/A", "Benchmark": "N/A", "Fund Name": "UNKNOWN"}
                            nearby = lines[max(0, j - 6): j + 6]
                            for near_line in nearby:
                                if "Manager:" in near_line:
                                    entry["Manager"] = near_line.split("Manager:")[1].strip()
                                if "Inception Date:" in near_line:
                                    match = re.search(r"(\d{2}/\d{2}/\d{4})", near_line)
                                    if match:
                                        entry["Inception Date"] = match.group(1)
                                if "Benchmark:" in near_line:
                                    entry["Benchmark"] = near_line.split("Benchmark:")[1].strip()
                            # Try to extract fund name from the first few lines
                            for k in range(max(0, j - 5), j):
                                candidate = lines[k].strip()
                                if len(candidate.split()) > 2 and not any(x in candidate for x in ["Manager", "Benchmark", "Date"]):
                                    entry["Fund Name"] = candidate
                                    break
                            metadata_index.append(entry)

                # === Phase 3: Scorecard block parsing ===
                for i in range(total_pages):
                    text = pdf.pages[i].extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.strip().split("\n")
                        if not lines:
                            continue

                        raw_line = lines[0]
                        clean_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist.*)", "", raw_line).strip()
                        norm_clean = normalize_name(clean_name)

                        # Fuzzy match fund_meta
                        match_key = None
                        if norm_clean in fund_meta:
                            match_key = norm_clean
                        else:
                            scores = [(k, simple_similarity(norm_clean, k)) for k in fund_meta]
                            best_match = max(scores, key=lambda x: x[1], default=(None, 0))
                            if best_match[1] > 0.6:
                                match_key = best_match[0]

                        if not match_key:
                            continue

                        meta = fund_meta[match_key]
                        meets_criteria = "placed on watchlist" not in block
                        criteria = []
                        percentile = None

                        for line in lines[1:]:
                            match = re.match(r"^(.*?)\s+(Pass|Review)(.*?)?$", line.strip())
                            if match:
                                metric = match.group(1).strip()
                                result = match.group(2).strip()
                                percent_match = re.search(r"\((\d{1,3})(st|nd|rd|th)? percentile\)", line)
                                if percent_match:
                                    percentile = percent_match.group(1) + "%"
                                criteria.append((metric, result))

                        # Fuzzy match metadata from global index
                        best_meta = {"Manager": "N/A", "Inception Date": "N/A", "Benchmark": "N/A"}
                        scores = [(normalize_name(m["Fund Name"]), simple_similarity(norm_clean, normalize_name(m["Fund Name"]))) for m in metadata_index]
                        scores = sorted(scores, key=lambda x: x[1], reverse=True)
                        if scores and scores[0][1] > 0.6:
                            best_index = [m for m in metadata_index if normalize_name(m["Fund Name"]) == scores[0][0]]
                            if best_index:
                                best_meta = best_index[0]

                        if criteria:
                            criteria_data.append({
                                **meta,
                                **best_meta,
                                "Peer Percentile": percentile or "N/A",
                                "Meets Criteria": "Yes" if meets_criteria else "No",
                                **{metric: result for metric, result in criteria}
                            })

        # === Final Display ===
        if criteria_data:
            df = pd.DataFrame(criteria_data)
            st.success(f"✅ Extracted {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download as CSV", data=csv, file_name="fund_criteria_results.csv", mime="text/csv")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
