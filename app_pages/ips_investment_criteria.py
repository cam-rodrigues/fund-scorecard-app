import streamlit as st
import pdfplumber
import re
from difflib import get_close_matches

def extract_short_name(name, words=5):
    return " ".join(name.split()[:words]).lower()

def run():
    st.set_page_config(page_title="Step 12: IPS + Ticker Match", layout="wide")
    st.title("Step 12: IPS Investment Criteria Screening + Ticker")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step12_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Step 1: Get Total Options from Page 1 ===
            page1_text = pdf.pages[0].extract_text()
            total_match = re.search(r"Total Options:\s*(\d+)", page1_text or "")
            declared_total = int(total_match.group(1)) if total_match else None

            # === Step 2: Find TOC Pages ===
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
                st.error("❌ Missing page numbers for required sections.")
                return

            # === Step 3: Extract Fund Scorecard ===
            lines_buffer = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text:
                    continue
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

            # === Step 4: Clean Watchlist + Invalid Names ===
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

            # === Step 6: IPS Screening ===
            def screen_ips(fund):
                name = fund["name"]
                metrics = {m[0]: m[1] for m in fund["metrics"]}
                is_passive = "bitcoin" in name.lower()

                def status(metric_name):
                    return metrics.get(metric_name, "Review")

                results = [
                    status("Manager Tenure"),
                    status("R-Squared (3Yr)") if is_passive else status("Excess Performance (3Yr)"),
                    status("Peer Return Rank (3Yr)"),
                    status("Sharpe Ratio Rank (3Yr)"),
                    status("Tracking Error Rank (3Yr)") if is_passive else status("Sortino Ratio Rank (3Yr)"),
                    status("R-Squared (5Yr)") if is_passive else status("Excess Performance (5Yr)"),
                    status("Peer Return Rank (5Yr)"),
                    status("Sharpe Ratio Rank (5Yr)"),
                    status("Tracking Error Rank (5Yr)") if is_passive else status("Sortino Ratio Rank (5Yr)"),
                    status("Expense Ratio Rank"),
                    "Pass"
                ]
                return results

            # === Step 7: Display Results ===
            st.subheader("IPS Investment Criteria Results + Ticker")
            for fund in cleaned_funds:
                ips_results = screen_ips(fund)
                fail_count = sum(1 for r in ips_results if r == "Review")

                if fail_count <= 4:
                    status_label = "✅ Passed IPS Screen"
                elif fail_count == 5:
                    status_label = "🟠 Informal Watch (IW)"
                else:
                    status_label = "🔴 Formal Watch (FW)"

                st.markdown(f"### {fund['name']}")
                st.markdown(f"- **Ticker:** `{fund['ticker']}`")
                for idx, res in enumerate(ips_results, start=1):
                    st.markdown(f"- **{idx}.** `{res}`")
                st.markdown(f"**Final IPS Status:** {status_label}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
