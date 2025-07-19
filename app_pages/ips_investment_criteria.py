import streamlit as st
import pdfplumber
import re
import pandas as pd
from difflib import get_close_matches

def extract_short_name(name, words=5):
    return " ".join(name.split()[:words]).lower()

def run():
    st.set_page_config(page_title="Step 14: IPS + Ticker + Reasoning", layout="wide")
    st.title("Step 14: IPS Investment Criteria with Ticker + Reasoning")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step14_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Page 1 Data ===
            page1_text = pdf.pages[0].extract_text()
            total_match = re.search(r"Total Options:\s*(\d+)", page1_text or "")
            declared_total = int(total_match.group(1)) if total_match else None

            # === Table of Contents (Page 2) ===
            toc_text = pdf.pages[1].extract_text()
            def find_page(title):
                for line in toc_text.split("\n"):
                    if title in line:
                        match = re.search(r"(\d+)$", line.strip())
                        return int(match.group(1)) if match else None
                return None

            scorecard_page = find_page("Fund Scorecard")
            perf_page = find_page("Fund Performance: Current vs. Proposed Comparison")
            if not scorecard_page or not perf_page:
                st.error("❌ Could not find required sections in Table of Contents.")
                return

            # === Extract Scorecard Section ===
            lines_buffer = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text or "Style Box Analysis" in text:
                    break
                lines_buffer.extend(text.split("\n"))

            skip_keywords = [
                "Criteria Threshold", "Portfolio manager", "must outperform", "must be in the top",
                "must be greater than", "Created with mpi Stylus"
            ]
            cleaned_lines = [line.strip() for line in lines_buffer if not any(kw in line for kw in skip_keywords)]

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
                    i += 14
                else:
                    i += 1

            # === Clean Names ===
            def clean_watchlist_text(name):
                name = re.sub(r"Fund Meets Watchlist Criteria\.", "", name)
                name = re.sub(r"Fund has been placed on watchlist.*", "", name)
                return name.strip()

            invalid_name_terms = [
                "FUND FACTS 3 YEAR ROLLING STYLE",
                "FUND FACTS 3 YEAR ROLLING STYLE ASSET LOADINGS (Returns-based)"
            ]

            cleaned_funds = []
            for f in fund_blocks:
                if any(term in f["name"].upper() for term in invalid_name_terms):
                    continue
                name = clean_watchlist_text(f["name"])
                if name:
                    cleaned_funds.append({"name": name, "metrics": f["metrics"]})

            # === Ticker Matching ===
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

            # === IPS Screening w/ Descriptions ===
            def screen_ips(fund):
                name = fund["name"]
                metrics_raw = {m[0]: (m[1], m[2]) for m in fund["metrics"]}
                is_passive = "bitcoin" in name.lower()

                def get(metric_name):
                    return metrics_raw.get(metric_name, ("Review", "No data"))

                results = []

                results.append(("Manager Tenure", *get("Manager Tenure")))

                if is_passive:
                    label = "R² (3Y)"
                    metric_result, metric_reason = get("R-Squared (3Yr)")
                else:
                    label = "3Y Performance"
                    metric_result, metric_reason = get("Excess Performance (3Yr)")
                results.append((label, metric_result, metric_reason))

                results.append(("3Y Peer Rank", *get("Peer Return Rank (3Yr)")))
                results.append(("3Y Sharpe", *get("Sharpe Ratio Rank (3Yr)")))

                if is_passive:
                    label = "Tracking Error (3Y)"
                    metric_result, metric_reason = get("Tracking Error Rank (3Yr)")
                else:
                    label = "3Y Sortino"
                    metric_result, metric_reason = get("Sortino Ratio Rank (3Yr)")
                results.append((label, metric_result, metric_reason))

                if is_passive:
                    label = "R² (5Y)"
                    metric_result, metric_reason = get("R-Squared (5Yr)")
                else:
                    label = "5Y Performance"
                    metric_result, metric_reason = get("Excess Performance (5Yr)")
                results.append((label, metric_result, metric_reason))

                results.append(("5Y Peer Rank", *get("Peer Return Rank (5Yr)")))
                results.append(("5Y Sharpe", *get("Sharpe Ratio Rank (5Yr)")))

                if is_passive:
                    label = "Tracking Error (5Y)"
                    metric_result, metric_reason = get("Tracking Error Rank (5Yr)")
                else:
                    label = "5Y Sortino"
                    metric_result, metric_reason = get("Sortino Ratio Rank (5Yr)")
                results.append((label, metric_result, metric_reason))

                results.append(("Expense Ratio", *get("Expense Ratio Rank")))
                results.append(("Investment Style", "Pass", "Automatically satisfied"))

                return results

            # === Display Output ===
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
                st.markdown(f"- **Ticker:** `{fund['ticker']}`")
                for idx, (label, result, reason) in enumerate(ips_results, start=1):
                    st.markdown(f"- **{idx}. {label}** → `{result}` — {reason}")
                st.markdown(f"**Final IPS Status:** {status_label}")
                st.markdown("---")

    # === Final IPS Table ===
    table_data = []
    
    for fund in fund_blocks:
        name = re.sub(r"Fund Meets Watchlist Criteria\.", "", fund["name"])
        name = re.sub(r"Fund has been placed on watchlist.*", "", name).strip()
        if not name or any(term in name.upper() for term in [
            "FUND FACTS 3 YEAR ROLLING STYLE",
            "FUND FACTS 3 YEAR ROLLING STYLE ASSET LOADINGS (Returns-based)"
        ]):
            continue
    
        fund["name"] = name
        ips_results = screen_ips(fund)
        fail_count = sum(1 for m in ips_results if m[1] == "Review")
    
        if fail_count <= 4:
            status_label = "Passed IPS Screen"
        elif fail_count == 5:
            status_label = "Informal Watch (IW)"
        else:
            status_label = "Formal Watch (FW)"
    
        row = {
            "Investment Option": name,
            "Ticker": fund.get("ticker", "Not Found"),
            "Time Period": "Q1 2025",  # Replace later with dynamic time_period if needed
            "Plan Assets": "$"
        }
        for i, (_, result, _) in enumerate(ips_results, start=1):
            row[str(i)] = result
        row["IPS Status"] = status_label
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    def color_metric(val):
        if val == "Pass":
            return "background-color: #d4edda"
        elif val == "Review":
            return "background-color: #f8d7da"
        return ""
    
    def color_status(val):
        if val == "Passed IPS Screen":
            return "background-color: #28a745; color: white"
        elif "Informal" in val:
            return "background-color: #fd7e14; color: white"
        elif "Formal" in val:
            return "background-color: #dc3545; color: white"
        return ""
    
    styled = df.style.applymap(color_metric, subset=[str(i) for i in range(1, 12)])
    styled = styled.applymap(color_status, subset=["IPS Status"])
    
    st.subheader("Final IPS Table")
    st.dataframe(styled, use_container_width=True)

    except Exception as e:
    st.error(f"❌ Error processing PDF: {e}")

    
