import streamlit as st
import pdfplumber
import re
import pandas as pd
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Steps: Convert & Cleanup", layout="wide")
    st.title("Steps 1-11")

    # Step 1 – Upload PDF
    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step3_upload")

    if uploaded_file:
        st.success("✅ MPI PDF successfully uploaded.")

        try:
            with pdfplumber.open(uploaded_file) as pdf:
                raw_text = pdf.pages[0].extract_text()

# Step 9 
                page1_text = pdf.pages[0].extract_text()
                total_match = re.search(r"Total Options:\s*(\d+)", page1_text or "")
                declared_total = int(total_match.group(1)) if total_match else None
                    
                
    # Step 3 – Remove boilerplate footer line
                cleaned_text = re.sub(
                    r"For Plan Sponsor use only.*?Created with mpi Stylus\.", "", raw_text, flags=re.DOTALL
                )

                st.subheader("Cleaned Text from Page 1")
                st.text(cleaned_text)

    # Step 2 – Extract Quarter-End Date
                quarter_match = re.search(r'(3/31|6/30|9/30|12/31)/20\d{2}', cleaned_text)
                if quarter_match:
                    date_str = quarter_match.group(0)
                    month_day = date_str[:5]
                    year = "20" + date_str[-2:]

                    quarter_map = {
                        "3/31": "Q1",
                        "6/30": "Q2",
                        "9/30": "Q3",
                        "12/31": "Q4"
                    }

                    quarter = quarter_map.get(date_str[:date_str.rfind("/")], "Unknown") + " " + date_str[-4:]
                else:
                    quarter = "Not found"

                # Extract Total Options
                total_match = re.search(r"Total Options:\s*(\d+)", cleaned_text)
                total_options = total_match.group(1) if total_match else "Not found"

                # Extract Prepared For
                prepared_for_match = re.search(r"Prepared For:\s*\n(.+)", cleaned_text)
                prepared_for = prepared_for_match.group(1).strip() if prepared_for_match else "Not found"

                # Extract Prepared By
                prepared_by_match = re.search(r"Prepared By:\s*\n(.+)", cleaned_text)
                prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else "Not found"

                # Display results
                st.subheader("Extracted Page 1 Summary")
                st.markdown(f"**Time Period:** {quarter}")
                st.markdown(f"**Total Options:** {total_options}")
                st.markdown(f"**Prepared For:** {prepared_for}")
                st.markdown(f"**Prepared By:** {prepared_by}")

    # Step 4 - Table of Contents
    # Page 2 – Table of Contents
                toc_text = pdf.pages[1].extract_text()
                
    # Step 5/6 – Remove irrelevant TOC lines
                lines = toc_text.split("\n")
                ignore_keywords = [
                    "Calendar Year", "Risk Analysis", "Style Box", "Returns Correlation",
                    "Fund Factsheets", "Definitions & Disclosures", "Past performance",
                    "Total Options", "http://", quarter.replace(" ", "/"),
                    "shares may be worth more/less than original cost",
                    "Returns assume reinvestment of all distributions at NAV"
                ]

                cleaned_toc_lines = [
                    line for line in lines
                    if not any(kw in line for kw in ignore_keywords)
                ]

                # Step 5 – Extract relevant section page numbers
                def find_page(section_title, toc_lines):
                    for line in toc_lines:
                        if section_title in line:
                            match = re.search(r"(\d+)$", line)
                            return int(match.group(1)) if match else None
                    return None

                perf_page = find_page("Fund Performance: Current vs. Proposed Comparison", cleaned_toc_lines)
                scorecard_page = find_page("Fund Scorecard", cleaned_toc_lines)

                # Display cleaned TOC + section page number
                st.subheader("Cleaned Table of Contents")
                for line in cleaned_toc_lines:
                    st.markdown(f"- {line}")

                # Find section pages
                def find_page_number(section_title, toc_text):
                    pattern = rf"{re.escape(section_title)}[\s\.]*?(\d+)"
                    match = re.search(pattern, toc_text)
                    return int(match.group(1)) if match else None

                perf_page = find_page_number("Fund Performance: Current vs. Proposed Comparison", toc_text)
                scorecard_page = find_page_number("Fund Scorecard", toc_text)

                # Display extracted results
                st.subheader("Extracted Sections")
                st.markdown(f"**Time Period:** {quarter}")
                st.markdown(f"**Fund Performance Section Page:** {perf_page if perf_page else 'Not found'}")
                st.markdown(f"**Fund Scorecard Section Page:** {scorecard_page if scorecard_page else 'Not found'}")

#Step 7
        
            toc_text = pdf.pages[1].extract_text()
            def find_page(section_title):
                for line in toc_text.split("\n"):
                    if section_title in line:
                        match = re.search(r"(\d+)$", line)
                        return int(match.group(1)) if match else None
                return None
            scorecard_page = find_page("Fund Scorecard")
            if not scorecard_page:
                st.error("❌ Could not find Fund Scorecard page.")
                return

            # --- Extract Investment Options + Metrics ---
            fund_blocks = []
            lines_buffer = []

            # Read all text from Fund Scorecard pages
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text:
                    continue
                lines_buffer.extend(text.split("\n"))

            # Clean up buffer
            cleaned_lines = []
            skip_keywords = [
                "Criteria Threshold",
                "Portfolio manager or management team",
                "must outperform its benchmark",
                "must be in the top 50%", "must be in the top 10%",
                "must be greater than 95%",
                "Created with mpi Stylus"
            ]

            for line in lines_buffer:
                if not any(kw in line for kw in skip_keywords):
                    cleaned_lines.append(line.strip())

            # Parse blocks based on "Manager Tenure" anchor
            fund_blocks = []
            i = 0
            while i < len(cleaned_lines):
                if "Manager Tenure" in cleaned_lines[i]:
                    if i == 0:
                        i += 1
                        continue
                    fund_name = cleaned_lines[i - 1].strip()
                    metrics_block = cleaned_lines[i:i + 14]
                    parsed_metrics = []

                    for m_line in metrics_block:
                        m = re.match(r"(.+?)\s+(Pass|Review)\s+(.*)", m_line)
                        if m:
                            metric_name = m.group(1).strip()
                            status = m.group(2).strip()
                            reason = m.group(3).strip()
                            parsed_metrics.append((metric_name, status, reason))

                    fund_blocks.append({
                        "name": fund_name,
                        "metrics": parsed_metrics
                    })

                    i += 14  # skip the block
                else:
                    i += 1

# --- Step 10: Remove Invalid Names (Not Actual Funds) ---
            invalid_name_terms = [
                "FUND FACTS 3 YEAR ROLLING STYLE",
                "FUND FACTS 3 YEAR ROLLING STYLE ASSET LOADINGS (Returns-based)"
            ]

            cleaned_funds = [
                f for f in fund_blocks
                if not any(term in f["name"].upper() for term in invalid_name_terms)
            ]

 # --- Step 11: Clean Watchlist Sentences from Fund Names ---
            def clean_watchlist_text(name):
                name = re.sub(r"Fund Meets Watchlist Criteria\.", "", name)
                name = re.sub(r"Fund has been placed on watchlist.*", "", name)
                return name.strip()

            final_funds = []
            for f in cleaned_funds:
                cleaned_name = clean_watchlist_text(f["name"])
                if cleaned_name:  # Only include if something remains
                    final_funds.append({
                        "name": cleaned_name,
                        "metrics": f["metrics"]
                    })
 # --- Step 9: Compare counts ---
            st.subheader("Double Check: Investment Option Count")
            st.markdown(f"- Declared in PDF (Page 1): **{declared_total if declared_total else 'Not found'}**")
            st.markdown(f"- Extracted from Scorecard (after cleanup): **{len(final_funds)}**")

            if declared_total is None:
                st.warning("⚠️ Could not find Total Options on Page 1.")
            elif declared_total == len(final_funds):
                st.success("✅ Number of Investment Options matches.")
            else:
                st.error("❌ Mismatch: PDF says one number, but we extracted a different number.")


            # --- Display results ---
            st.subheader("Cleaned Investment Options (Watchlist stripped)")
            for fund in final_funds:
                st.markdown(f"### {fund['name']}")
                for metric in fund["metrics"]:
                    st.markdown(f"- **{metric[0]}** → {metric[1]} — {metric[2]}")
                st.markdown("---")

            # === Step 5: Extract Tickers from Performance Section ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if not text or "Fund Factsheets" in text:
                    break
                perf_lines.extend(text.split("\n"))

            all_perf_lines = [line.strip() for line in perf_lines if len(line.strip()) > 5]

            for fund in cleaned_funds:
                short = extract_short_name(fund["name"])
                match_line = next((
                    line for line in all_perf_lines
                    if short in extract_short_name(line)
                ), None)

                if match_line:
                    m = re.search(r"\b([A-Z]{5})\b", match_line)
                    fund["ticker"] = m.group(1) if m else "Not Found"
                else:
                    fund["ticker"] = "Not Found"

    # === Step 12 - IPS Screening Logic ===
            def screen_ips(fund):
                name = fund["name"]
                metrics_raw = {m[0]: (m[1], m[2]) for m in fund["metrics"]}
                metrics = {m[0]: m[1] for m in fund["metrics"]}

                is_passive = "bitcoin" in name.lower()

                def get(metric_name):
                    return metrics_raw.get(metric_name, ("Review", "No data"))

                results = []

                # 1: Manager Tenure
                results.append(("Manager Tenure", *get("Manager Tenure")))

                # 2: 3Y Performance or 3Y R²
                if is_passive:
                    label = "R² (3Y)"
                    metric_result, metric_reason = get("R-Squared (3Yr)")
                else:
                    label = "3Y Performance"
                    metric_result, metric_reason = get("Excess Performance (3Yr)")
                results.append((label, metric_result, metric_reason))
                
                # 3: 3Y Peer Rank
                results.append(("3Y Peer Rank", *get("Peer Return Rank (3Yr)")))

                # 4: 3Y Sharpe
                results.append(("3Y Sharpe", *get("Sharpe Ratio Rank (3Yr)")))

                # 5: 3Y Sortino or Tracking Error
                if is_passive:
                    label = "Tracking Error (3Y)"
                    metric_result, metric_reason = get("Tracking Error Rank (3Yr)")
                else:
                    label = "3Y Sortino"
                    metric_result, metric_reason = get("Sortino Ratio Rank (3Yr)")
                results.append((label, metric_result, metric_reason))


                # 6: 5Y Performance or 5Y R²
                if is_passive:
                    label = "R² (5Y)"
                    metric_result, metric_reason = get("R-Squared (5Yr)")
                else:
                    label = "5Y Performance"
                    metric_result, metric_reason = get("Excess Performance (5Yr)")
                results.append((label, metric_result, metric_reason))

                # 7: 5Y Peer Rank
                results.append(("5Y Peer Rank", *get("Peer Return Rank (5Yr)")))

                # 8: 5Y Sharpe
                results.append(("5Y Sharpe", *get("Sharpe Ratio Rank (5Yr)")))

                # 9: 5Y Sortino or Tracking Error
                if is_passive:
                    label = "Tracking Error (5Y)"
                    metric_result, metric_reason = get("Tracking Error Rank (5Yr)")
                else:
                    label = "5Y Sortino"
                    metric_result, metric_reason = get("Sortino Ratio Rank (5Yr)")
                results.append((label, metric_result, metric_reason))

                # 10: Expense Ratio
                results.append(("Expense Ratio", *get("Expense Ratio Rank")))

                # 11: Investment Style = always Pass
                results.append(("Investment Style", "Pass", "Automatically satisfied"))

                return results

            # === Display IPS Results ===
            st.subheader("IPS Results with Reasoning")
            for fund in cleaned_funds:
                ips_results = screen_ips(fund)
                fail_count = sum(1 for m in ips_results if m[1] == "Review")

                if fail_count <= 4:
                    status_label = "✅ Passed IPS Screen"
                elif fail_count == 5:
                    status_label = "🟠 Informal Watch (IW)"
                else:
                    status_label = "🔴 Formal Watch (FW)"

                st.markdown(f"### {fund['name']}")
                for idx, (label, result, reason) in enumerate(ips_results, start=1):
                    st.markdown(f"- **{idx}. {label}** → `{result}` — {reason}")
                st.markdown(f"**Final IPS Status:** {status_label}")
                st.markdown("---")
            
        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")
