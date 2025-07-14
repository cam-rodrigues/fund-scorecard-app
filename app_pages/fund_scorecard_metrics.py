import streamlit as st
import pdfplumber
import pandas as pd
import re

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

            fund_type_phrases = [
                "Large Cap Growth", "Large Cap Value", "Large Blend",
                "Mid Cap Growth", "Mid Cap Value", "Mid Cap Blend",
                "Small Cap Growth", "Small Cap Value", "Small Blend",
                "Target-Date Retirement", "Target-Date 2025", "Target-Date 2030", "Target-Date 2040",
                "Target-Date 2045", "Target-Date 2050", "Target-Date 2055", "Target-Date 2060",
                "Intermediate Core Bond", "Intermediate Core-Plus Bond",
                "Inflation-Protected Bond", "Multisector Bond", "Global Bond", "Commodities Broad Basket",
                "Real Estate", "International", "Emerging Markets", "Equity", "Fixed Income", "Stock", "Bond"
            ]

            share_class_keywords = ["Admiral", "Instl", "Institutional", "R6", "Z", "I", "K", "N"]

            with pdfplumber.open(uploaded_file) as pdf:
                total_pages = len(pdf.pages)

                # === Zone 1: First 15 pages – Fund Name + Ticker + Style Box + Fund Type ===
                for i in range(min(15, total_pages)):
                    text = pdf.pages[i].extract_text()
                    if not text:
                        continue
                    lines = text.split("\n")

                    for j, line in enumerate(lines):
                        ticker_match = re.match(r"^(.*?)([A-Z]{4,6})$", line.strip())
                        if ticker_match and j + 1 < len(lines):
                            fund_name = ticker_match.group(1).strip()
                            ticker = ticker_match.group(2).strip()
                            style_box_line = lines[j + 1].strip()

                            fund_type = next((ftype for ftype in fund_type_phrases if ftype.lower() in style_box_line.lower()), "N/A")
                            share_class = next((w for w in fund_name.split() if w in share_class_keywords), "N/A")

                            fund_meta[fund_name] = {
                                "Ticker": ticker,
                                "Style Box": style_box_line if style_box_line else "N/A",
                                "Fund Type": fund_type,
                                "Share Class": share_class,
                                "Benchmark": "N/A",
                                "Manager": "N/A",
                                "Inception Date": "N/A"
                            }

                # === Zone 2: Scorecard Pages – Criteria Results ===
                for i in range(total_pages):
                    text = pdf.pages[i].extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.strip().split("\n")
                        if not lines:
                            continue

                        raw_fund_line = lines[0]
                        clean_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist.*)", "", raw_fund_line).strip()
                        fund_name = clean_name

                        match_key = next((k for k in fund_meta if k.lower() in fund_name.lower()), fund_name)
                        meta = fund_meta.get(match_key, {})

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

                        if criteria:
                            criteria_data.append({
                                "Fund Name": fund_name,
                                "Ticker": meta.get("Ticker", "N/A"),
                                "Style Box": meta.get("Style Box", "N/A"),
                                "Fund Type": meta.get("Fund Type", "N/A"),
                                "Share Class": meta.get("Share Class", "N/A"),
                                "Manager": meta.get("Manager", "N/A"),
                                "Inception Date": meta.get("Inception Date", "N/A"),
                                "Benchmark": meta.get("Benchmark", "N/A"),
                                "Peer Percentile": percentile or "N/A",
                                "Meets Criteria": "Yes" if meets_criteria else "No",
                                **{metric: result for metric, result in criteria}
                            })

                # === Zone 3: Last 20 pages – Benchmark, Manager, Inception Date ===
                for i in range(total_pages - 20, total_pages):
                    text = pdf.pages[i].extract_text()
                    if not text:
                        continue
                    lines = text.split("\n")

                    for j, line in enumerate(lines):
                        if "Manager:" in line:
                            manager = line.split("Manager:")[1].strip()
                            name_line = lines[j - 1].strip() if j > 0 else ""
                            match_key = next((k for k in fund_meta if k.lower() in name_line.lower()), None)
                            if match_key:
                                fund_meta[match_key]["Manager"] = manager

                        if "Inception Date:" in line:
                            date_match = re.search(r"Inception Date:\s*(\d{2}/\d{2}/\d{4})", line)
                            if date_match:
                                inception = date_match.group(1)
                                name_line = lines[j - 1].strip() if j > 0 else ""
                                match_key = next((k for k in fund_meta if k.lower() in name_line.lower()), None)
                                if match_key:
                                    fund_meta[match_key]["Inception Date"] = inception

                        if "Benchmark:" in line:
                            benchmark = line.split("Benchmark:")[1].strip()
                            name_line = lines[j - 1].strip() if j > 0 else ""
                            match_key = next((k for k in fund_meta if k.lower() in name_line.lower()), None)
                            if match_key:
                                fund_meta[match_key]["Benchmark"] = benchmark

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
