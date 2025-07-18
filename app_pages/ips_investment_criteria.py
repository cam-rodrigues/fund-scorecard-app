import streamlit as st
import pdfplumber
import re
from difflib import get_close_matches

def run():
    st.set_page_config(page_title="Step 12: IPS Criteria Screening", layout="wide")
    st.title("Step 12: IPS Investment Criteria Screening + Ticker Detection")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"], key="step12_upload")
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # === Extract Total Options ===
            page1_text = pdf.pages[0].extract_text()
            total_match = re.search(r"Total Options:\s*(\d+)", page1_text or "")
            declared_total = int(total_match.group(1)) if total_match else None

            # === Extract TOC Sections ===
            toc_text = pdf.pages[1].extract_text()
            def find_page(section_title):
                for line in toc_text.split("\n"):
                    if section_title in line:
                        match = re.search(r"(\d+)$", line)
                        return int(match.group(1)) if match else None
                return None

            scorecard_page = find_page("Fund Scorecard")
            perf_page = find_page("Fund Performance: Current vs. Proposed Comparison")
            if not scorecard_page or not perf_page:
                st.error("❌ Could not find required pages.")
                return

            # === Pull Scorecard Section ===
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
            cleaned_lines = [
                line.strip() for line in lines_buffer
                if not any(kw in line for kw in skip_keywords)
            ]

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

            # === Ticker Extraction from Performance Section ===
            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if not text or "Fund Factsheets" in text:
                    break
                perf_lines.extend(text.split("\n"))

            def short_key(name):
                return " ".join(name.split()[:5])

            perf_lookup = {}
            for fund in cleaned_funds:
                key = short_key(fund["name"])
                match = get_close_matches(key, perf_lines, n=1, cutoff=0.7)
                if match:
                    line = match[0]
                    m = re.search(r"\b([A-Z]{5})\b", line)
                    fund["ticker"] = m.group(1) if m else "Not Found"
                else:
                    fund["ticker"] = "Not Found"

            # === IPS Screening Logic ===
            def screen_ips(fund):
                name = fund["name"]
                metrics = {m[0]: m[1] for m in fund["metrics"]}
                is_passive = "bitcoin" in name.lower()

                def status(metric_name):
                    return metrics.get(metric_name, "Review")

                results = []
                results.append(status("Manager Tenure"))
                results.append(status("R-Squared (3Yr)") if is_passive else status("Excess Performance (3Yr)"))
                results.append(status("Peer Return Rank (3Yr)"))
                results.append(status("Sharpe Ratio Rank (3Yr)"))
                results.append(status("Tracking Error Rank (3Yr)") if is_passive else status("Sortino Ratio Rank (3Yr)"))
                results.append(status("R-Squared (5Yr)") if is_passive else status("Excess Performance (5Yr)"))
                results.append(status("Peer Return Rank (5Yr)"))
                results.append(status("Sharpe Ratio Rank (5Yr)"))
                results.append(status("Tracking Error Rank (5Yr)") if is_passive else status("Sortino Ratio Rank (5Yr)"))
                results.append(status("Expense Ratio Rank"))
                results.append("Pass")  # Investment Style

                return results

            # === Display Final Output ===
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
                    color = "green" if res == "Pass" else "red"
                    st.markdown(f"- **{idx}.** `{res}`", unsafe_allow_html=True)
                st.markdown(f"**Final IPS Status:** {status_label}")
                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
