import streamlit as st
import pdfplumber
import re
from difflib import SequenceMatcher
import pandas as pd

def run():
    st.title("IPS Write-Up Tool")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="upload_mpi")
    if not uploaded_file:
        st.stop()

    with pdfplumber.open(uploaded_file) as pdf:
        # === Step 1: Metadata ===
        st.subheader("Step 1: PDF Metadata")
        st.write("**Total Pages:**", len(pdf.pages))

#------------------------------------------------------------------------------------------------------------------

        # === Step 2: Page 1 Extraction ===
        st.subheader("Step 2: Pg 1")
        page1 = pdf.pages[0]
        text = page1.extract_text()

        # Determine Quarter
        quarter = "Unknown"
        if "3/31/20" in text:
            quarter = "Q1"
        elif "6/30/20" in text:
            quarter = "Q2"
        elif "9/30/20" in text:
            quarter = "Q3"
        elif "12/31/20" in text:
            quarter = "Q4"

        st.write("**Quarter:**", quarter)

        # Total Options
        total_match = re.search(r"Total Options:\s*(\d+)", text)
        total_options = total_match.group(1) if total_match else "Not found"
        st.write("**Total Investment Options:**", total_options)

        # Prepared For
        prepared_for_match = re.search(r"Prepared For:\s*\n(.+)", text)
        prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else "Not found"
        st.write("**Prepared For:**", prepared_for)

        # Prepared By
        prepared_by_match = re.search(r"Prepared By:\s*\n(.+)", text)
        prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else "Not found"
        st.write("**Prepared By:**", prepared_by)

#------------------------------------------------------------------------------------------------------------------

        # === Step 4: Pg 2 - Table of Contents ===
        st.subheader("Step 4: Pg 2 - Table of Contents")
        page2 = pdf.pages[1]
        text2 = page2.extract_text()

        fund_perf_pg = "Not found"
        fund_scorecard_pg = "Not found"

        for line in text2.split("\n"):
            if "Fund Performance: Current vs. Proposed Comparison" in line:
                match = re.search(r"(\d+)$", line)
                if match:
                    fund_perf_pg = int(match.group(1))
            if "Fund Scorecard" in line:
                match = re.search(r"(\d+)$", line)
                if match:
                    fund_scorecard_pg = int(match.group(1))

        st.write("**Fund Performance Page:**", fund_perf_pg)
        st.write("**Fund Scorecard Page:**", fund_scorecard_pg)

#------------------------------------------------------------------------------------------------------------------

        # === Step 5: Fund Scorecard Section ===
        st.subheader("Step 5: Fund Scorecard Section")

        metrics_data = []
        metrics_header = []
        fund_blocks = []

        # Text cleaning pattern
        fund_status_pattern = re.compile(
            r"\s+(Fund Meets Watchlist Criteria\.|Fund has been placed on watchlist for not meeting.+)", re.IGNORECASE)

        # Read all pages starting from Fund Scorecard page
        for i in range(fund_scorecard_pg - 1, len(pdf.pages)):
            page = pdf.pages[i]
            text = page.extract_text()
            if not text or "Fund Scorecard" not in text:
                break

            lines = text.split("\n")

            # Capture Criteria Threshold section (appears once)
            if not metrics_header:
                for j in range(len(lines)):
                    if "Criteria Threshold" in lines[j]:
                        metrics_header = lines[j+1:j+15]
                        break

            # Capture fund blocks: look for lines starting with a metric, backtrack for fund name
            for j in range(len(lines)):
                if lines[j].startswith("Manager Tenure"):
                    raw_fund_line = lines[j-1].strip()
                    # Clean extra status text from the same line
                    fund_name = fund_status_pattern.sub("", raw_fund_line).strip()
                    if "criteria threshold" in fund_name.lower():
                        continue  # skip bad block that grabbed threshold box


                    fund_metrics = []
                    for k in range(j, j+14):
                        if k >= len(lines): break
                        metric_line = lines[k]
                        match = re.match(r"(.+?)\s+(Pass|Review)\s+(.*)", metric_line)
                        if match:
                            metric_name, status, reason = match.groups()
                            fund_metrics.append({
                                "Metric": metric_name.strip(),
                                "Status": status,
                                "Reason": reason.strip()
                            })
                    fund_blocks.append({
                        "Fund Name": fund_name,
                        "Metrics": fund_metrics
                    })

        # Display criteria header
        if metrics_header:
            st.markdown("**Criteria Threshold (14 Metrics):**")
            for item in metrics_header:
                st.markdown(f"- {item}")

        # Display fund blocks
        for block in fund_blocks:
            st.markdown(f"**{block['Fund Name']}**")
            for metric in block["Metrics"]:
                st.write(f"- {metric['Metric']}: **{metric['Status']}** – {metric['Reason']}")
                
#------------------------------------------------------------------------------------------------------------------
        
        # === Step 7: Double Check ===
        st.subheader("Step 7: Double Check")

        num_extracted_funds = len(fund_blocks)
        st.write("**Investment Options Extracted:**", num_extracted_funds)

        try:
            total_expected = int(total_options)
            if num_extracted_funds == total_expected:
                st.success(f"✅ Count matches: {num_extracted_funds} funds found.")
            else:
                st.warning(f"⚠️ Count mismatch: Found {num_extracted_funds}, but expected {total_expected}.")
        except:
            st.error("❌ Unable to validate count due to unreadable 'Total Options' value.")


#------------------------------------------------------------------------------------------------------------------

        # === Step 8: IPS Investment Criteria Screening ===
        st.subheader("Step 8: IPS Investment Criteria Screening")

        ips_criteria = [
            "Manager Tenure ≥ 3 years",
            "3-Year Performance > Benchmark / +3-Year R² > 95%",
            "3-Year Performance > 50% of Peers",
            "3-Year Sharpe Ratio > 50% of Peers",
            "3-Year Sortino Ratio > 50% of Peers / +3-Year Tracking Error < 90% of Peers",
            "5-Year Performance > Benchmark / +5-Year R² > 95%",
            "5-Year Performance > 50% of Peers",
            "5-Year Sharpe Ratio > 50% of Peers",
            "5-Year Sortino Ratio > 50% of Peers / +5-Year Tracking Error < 90% of Peers",
            "Expense Ratio < 50% of Peers",
            "Investment Style aligns with fund objectives"
        ]

        st.markdown("**IPS Investment Criteria:**")
        for i, crit in enumerate(ips_criteria, 1):
            st.markdown(f"{i}. {crit}")

        # Define mappings to fund scorecard metric labels
        def map_metric_names(fund_type):
            if fund_type == "Passive":
                return [
                    "Manager Tenure",
                    "R² (3Yr)",
                    "Return Rank (3Yr)",
                    "Sharpe Ratio Rank (3Yr)",
                    "Tracking Error Rank (3Yr)",
                    "R² (5Yr)",
                    "Return Rank (5Yr)",
                    "Sharpe Ratio Rank (5Yr)",
                    "Tracking Error Rank (5Yr)",
                    "Expense Ratio Rank",
                    "Investment Style"
                ]
            else:  # Active
                return [
                    "Manager Tenure",
                    "Excess Performance (3Yr)",
                    "Return Rank (3Yr)",
                    "Sharpe Ratio Rank (3Yr)",
                    "Sortino Ratio Rank (3Yr)",
                    "Excess Performance (5Yr)",
                    "Return Rank (5Yr)",
                    "Sharpe Ratio Rank (5Yr)",
                    "Sortino Ratio Rank (5Yr)",
                    "Expense Ratio Rank",
                    "Investment Style"
                ]

        # Evaluate IPS compliance for each fund
        for block in fund_blocks:
            fund_name = block["Fund Name"]
            fund_type = "Passive" if "bitcoin" in fund_name.lower() else "Active"
            expected_metrics = map_metric_names(fund_type)

            metric_lookup = {m["Metric"]: m["Status"] for m in block["Metrics"]}

            ips_results = []
            for label in expected_metrics[:-1]:  # first 10 metrics
                status = metric_lookup.get(label, "Review")
                ips_results.append("Pass" if status == "Pass" else "Fail")
            ips_results.append("Pass")  # Metric 11 always passes

            fail_count = ips_results.count("Fail")
            if fail_count <= 4:
                overall_status = "Passed IPS Screen"
            elif fail_count == 5:
                overall_status = "Informal Watch (IW)"
            else:
                overall_status = "Formal Watch (FW)"

            # Display results
            st.markdown(f"### {fund_name}")
            st.write(f"**Fund Type:** {fund_type}")
            for i, status in enumerate(ips_results, 1):
                st.write(f"- Metric {i}: {status}")
            st.write(f"**Overall IPS Status:** `{overall_status}`")


#------------------------------------------------------------------------------------------------------------------
        
        # === Step 9: Fund Performance: Current vs. Proposed Comparison Section ===
        st.subheader("Step 9: Fund Performance: Current vs. Proposed Comparison Section")

        if fund_perf_pg == "Not found":
            st.error("❌ Could not find the starting page for 'Fund Performance: Current vs. Proposed Comparison'")
        else:
            i = fund_perf_pg - 1  # Convert to 0-based index
            page = pdf.pages[i]
            text = page.extract_text()

            if text and "Fund Performance: Current vs. Proposed Comparison" in text:
                st.markdown(f"**Found section on page {i + 1}**")
                st.text(text[:2000])  # Display first part of the page for verification
            else:
                st.warning(f"⚠️ The text on page {i + 1} does not contain the expected heading. Double-check TOC accuracy.")
                st.text(text[:2000] if text else "No text found on this page.")

#-----------------------------------------------------------------------------------------------------------------

        # === Step 9.4 Redo: Match Investment Option Names & Extract Tickers ===
        st.subheader("Step 9.4: Match Investment Option Names Between Sections")
        
        # Pull fund names from previous Scorecard block
        scorecard_names = [block["Fund Name"] for block in fund_blocks]
        
        # Step 1: Read all pages in Fund Performance section (until heading changes)
        perf_lines = []
        reading = False
        
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                if "Fund Performance: Current vs. Proposed Comparison" in text:
                    reading = True
                elif reading and any(kw in text for kw in [
                    "Risk Analysis", "Fund Scorecard", "Definitions & Disclosures", "Table of Contents"
                ]):
                    break
                if reading:
                    perf_lines.extend(text.split("\n"))
        
        # Step 2: Filter candidate lines
        def is_potential_fund_line(line):
            if not (15 <= len(line) <= 90):
                return False
            if any(kw in line.lower() for kw in [
                "matrix", "disclosure", "calendar year", "page", "style", "returns", "mpt statistics"
            ]):
                return False
            return True
        
        clean_lines = [line.strip() for line in perf_lines if is_potential_fund_line(line)]
        
        # Step 3: Fuzzy match each fund name and extract ticker if present
        match_data = []
        for score_name in scorecard_names:
            best_score = 0
            best_line = ""
            best_ticker = ""
            for line in clean_lines:
                score = SequenceMatcher(None, score_name.lower(), line.lower()).ratio()
                if score > best_score:
                    best_score = score
                    ticker_match = re.search(r"\b[A-Z]{5}\b", line)
                    best_ticker = ticker_match.group(0) if ticker_match else ""
                    best_line = re.sub(r"\b[A-Z]{5}\b", "", line).strip()
            match_data.append({
                "Fund Scorecard Name": score_name,
                "Matched Line (Fund Performance)": best_line,
                "Extracted Ticker": best_ticker,
                "Match Score (0–100)": round(best_score * 100),
                "Matched": "✅" if best_score >= 0.60 else "❌"
            })
        
        df_matches = pd.DataFrame(match_data)
        st.dataframe(df_matches)


#-----------------------------------------------------------------------------------------------------------------

        # === Step 9.5: Category and Benchmark ===
        st.subheader("Step 9.5: Extract Category and Benchmark for Each Fund")
        
        scorecard_names = [block["Fund Name"] for block in fund_blocks]
        
        # Step 1: Extract all words in Fund Performance section (until heading changes)
        lines_with_positions = []
        reading = False
        
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                if "Fund Performance: Current vs. Proposed Comparison" in text:
                    reading = True
                elif reading and any(kw in text for kw in [
                    "Risk Analysis", "Fund Scorecard", "Definitions & Disclosures", "Table of Contents"
                ]):
                    break
                if reading:
                    words = page.extract_words()
                    line_map = {}
                    for w in words:
                        y0 = round(w['top'], 1)
                        if y0 not in line_map:
                            line_map[y0] = []
                        line_map[y0].append(w['text'])
                    for y in sorted(line_map.keys()):
                        line_text = " ".join(line_map[y])
                        lines_with_positions.append((y, line_text))
        
        # Step 2: Match names and extract ticker + category (above) + benchmark (below)
        match_data = []
        for name in scorecard_names:
            best_score = 0
            best_idx = -1
            best_line = ""
            best_ticker = ""
        
            for i, (y, line) in enumerate(lines_with_positions):
                score = SequenceMatcher(None, name.lower(), line.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_idx = i
                    ticker_match = re.search(r"\b[A-Z]{5}\b", line)
                    best_ticker = ticker_match.group(0) if ticker_match else ""
                    best_line = re.sub(r"\b[A-Z]{5}\b", "", line).strip()
        
            # Extract adjacent category and benchmark lines
            category_line = lines_with_positions[best_idx - 1][1] if best_idx > 0 else ""
            benchmark_line = lines_with_positions[best_idx + 1][1] if best_idx + 1 < len(lines_with_positions) else ""
        
            match_data.append({
                "Fund Scorecard Name": name,
                "Matched Name (Fund Performance)": best_line,
                "Extracted Ticker": best_ticker,
                "Category": category_line,
                "Benchmark": benchmark_line,
                "Match Score (0–100)": round(best_score * 100),
                "Matched": "✅" if best_score >= 0.60 else "❌"
            })
        
        df_95 = pd.DataFrame(match_data)
        st.dataframe(df_95)
