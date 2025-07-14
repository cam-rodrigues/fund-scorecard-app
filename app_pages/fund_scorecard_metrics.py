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
        with st.spinner("Extracting fund details and criteria..."):
            criteria_data = []
            fund_to_ticker = {}
            fund_to_category = {}
            fund_to_benchmark = {}
            fund_to_manager = {}
            fund_to_inception = {}

            # Step 1: Build mappings from PDF
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    lines = text.split("\n")

                    for i, line in enumerate(lines):
                        # Ticker and style box (appear back-to-back)
                        ticker_match = re.match(r"^(.*?)([A-Z]{4,6})\s*$", line.strip())
                        if ticker_match and i + 1 < len(lines):
                            fund_name = ticker_match.group(1).strip()
                            ticker = ticker_match.group(2).strip()
                            fund_to_ticker[fund_name] = ticker

                            style_box_line = lines[i + 1].strip()
                            if any(x in style_box_line for x in ["Large", "Mid", "Small", "Value", "Growth", "Blend", "Target-Date"]):
                                fund_to_category[fund_name] = style_box_line

                        # Benchmark
                        if "Benchmark:" in line:
                            parts = line.split("Benchmark:")
                            if len(parts) > 1:
                                benchmark = parts[1].strip()
                                last_fund = list(fund_to_ticker.keys())[-1] if fund_to_ticker else None
                                if last_fund:
                                    fund_to_benchmark[last_fund] = benchmark

                        # Inception Date
                        if "Inception Date:" in line:
                            date_match = re.search(r"Inception Date:\s*(\d{2}/\d{2}/\d{4})", line)
                            if date_match:
                                inception = date_match.group(1)
                                last_fund = list(fund_to_ticker.keys())[-1] if fund_to_ticker else None
                                if last_fund:
                                    fund_to_inception[last_fund] = inception

                        # Manager Name
                        if "Manager:" in line:
                            manager_match = re.search(r"Manager:\s*(.*)", line)
                            if manager_match:
                                manager = manager_match.group(1).strip()
                                last_fund = list(fund_to_ticker.keys())[-1] if fund_to_ticker else None
                                if last_fund:
                                    fund_to_manager[last_fund] = manager

                # Step 2: Parse Fund Scorecard Section
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text or "Fund Scorecard" not in text:
                        continue

                    blocks = re.split(r"\n(?=[^\n]*?Fund (?:Meets Watchlist Criteria|has been placed on watchlist))", text)

                    for block in blocks:
                        lines = block.strip().split("\n")
                        if not lines:
                            continue

                        raw_fund_line = lines[0]
                        clean_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist.*)", "", raw_fund_line).strip()
                        fund_name = clean_name if len(clean_name.split()) > 2 else raw_fund_line

                        # Match fund metadata from earlier pages
                        ticker = "N/A"
                        style_box = "N/A"
                        benchmark = "N/A"
                        manager = "N/A"
                        inception = "N/A"
                        match_key = None

                        for key in fund_to_ticker:
                            if key.lower() in fund_name.lower():
                                match_key = key
                                ticker = fund_to_ticker.get(key, "N/A")
                                style_box = fund_to_category.get(key, "N/A")
                                benchmark = fund_to_benchmark.get(key, "N/A")
                                manager = fund_to_manager.get(key, "N/A")
                                inception = fund_to_inception.get(key, "N/A")
                                break

                        # Improved Fund Type extraction
                        fund_type_phrases = [
                            "Large Cap Growth", "Large Cap Value", "Large Blend",
                            "Mid Cap Growth", "Mid Cap Value", "Mid Cap Blend",
                            "Small Cap Growth", "Small Cap Value", "Small Blend",
                            "Target-Date Retirement", "Target-Date 2025", "Target-Date 2030", "Target-Date 2040",
                            "Target-Date 2045", "Target-Date 2050", "Target-Date 2055", "Target-Date 2060", "Target-Date 2065",
                            "Intermediate Core Bond", "Intermediate Core-Plus Bond",
                            "Inflation-Protected Bond", "Multisector Bond", "Global Bond", "Commodities Broad Basket",
                            "Real Estate", "International", "Emerging Markets", "Equity", "Fixed Income"
                        ]
                        fund_type = next((phrase for phrase in fund_type_phrases if phrase.lower() in block.lower()), "N/A")

                        # Share class keywords
                        share_class_keywords = ["Admiral", "Instl", "Institutional", "R6", "Z", "I", "K", "N"]
                        words = fund_name.split()
                        share_class = next((w for w in words if w in share_class_keywords), "N/A")

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
                                "Ticker": ticker,
                                "Style Box": style_box,
                                "Fund Type": fund_type,
                                "Share Class": share_class,
                                "Manager": manager,
                                "Inception Date": inception,
                                "Benchmark": benchmark,
                                "Peer Percentile": percentile or "N/A",
                                "Meets Criteria": "Yes" if meets_criteria else "No",
                                **{metric: result for metric, result in criteria}
                            })

        if criteria_data:
            df = pd.DataFrame(criteria_data)
            st.success(f"✅ Found {len(df)} fund entries.")
            st.dataframe(df, use_container_width=True)

            with st.expander("Download Results"):
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download as CSV", data=csv, file_name="fund_criteria_results.csv", mime="text/csv")
        else:
            st.warning("No fund entries found in the uploaded PDF.")
    else:
        st.info("Please upload an MPI fund scorecard PDF to begin.")
