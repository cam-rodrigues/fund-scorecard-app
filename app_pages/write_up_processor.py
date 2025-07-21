import streamlit as st
import pdfplumber
import re
import pandas as pd
from rapidfuzz import fuzz

def process_mpi(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        # === Page 1 ===
        first_page_text = pdf.pages[0].extract_text()
        date_match = re.search(r"(3/31/20\d{2}|6/30/20\d{2}|9/30/20\d{2}|12/31/20\d{2})", first_page_text)
        if date_match:
            date_str = date_match.group(1)
            year = date_str[-4:]
            quarter = f"Q{['3/31', '6/30', '9/30', '12/31'].index(date_str[:5]) + 1}, {year}"
        else:
            date_str = "Not found"
            quarter = "Unknown"

        st.session_state["report_quarter"] = quarter
        st.session_state["total_options"] = int(re.search(r"Total Options:\s*(\d+)", first_page_text).group(1)) if re.search(r"Total Options:\s*(\d+)", first_page_text) else None
        st.session_state["prepared_for"] = re.search(r"Prepared For:\s*\n(.*)", first_page_text).group(1).strip() if re.search(r"Prepared For:\s*\n(.*)", first_page_text) else "Not found"
        st.session_state["prepared_by"] = re.search(r"Prepared By:\s*\n(.*)", first_page_text).group(1).strip() if re.search(r"Prepared By:\s*\n(.*)", first_page_text) else "Not found"

        # === Table of Contents (Page 2) ===
        toc_text = pdf.pages[1].extract_text()
        toc_entries = re.findall(r"(Fund Performance: Current vs\. Proposed Comparison|Fund Scorecard|Fund Factsheets).*?(\d{1,3})", toc_text)
        toc_pages = {"Fund Performance": None, "Fund Scorecard": None, "Fund Factsheets": None}
        for title, page in toc_entries:
            toc_pages[title.split(":")[0]] = int(page)
        st.session_state["toc_pages"] = toc_pages

        # === Fund Scorecard Metrics Threshold ===
        metrics_list = []
        fund_scorecard_pg = toc_pages["Fund Scorecard"]
        if fund_scorecard_pg:
            scorecard_text = pdf.pages[fund_scorecard_pg - 1].extract_text()
            criteria_match = re.search(r"Criteria Threshold\s*\n((?:.*\n){10,20})", scorecard_text)
            if criteria_match:
                metrics_list = [line.strip() for line in criteria_match.group(1).strip().split("\n") if line.strip()]
        st.session_state["fund_scorecard_metrics"] = metrics_list
        st.session_state["fund_scorecard_table"] = pd.DataFrame({
            "Metric #": list(range(1, len(metrics_list) + 1)),
            "Fund Scorecard Metric": metrics_list
        })

        # === Fund Scorecard Blocks ===
        fund_blocks = []
        fund_status_pattern = re.compile(r"\s+(Fund Meets Watchlist Criteria\.|Fund has been placed on watchlist for not meeting.+)", re.IGNORECASE)
        start = toc_pages["Fund Scorecard"] - 1
        end = toc_pages["Fund Factsheets"] - 2 if toc_pages["Fund Factsheets"] else len(pdf.pages) - 1

        for i in range(start, end + 1):
            lines = pdf.pages[i].extract_text().split("\n")
            for j in range(len(lines)):
                if lines[j].startswith("Manager Tenure") and j > 0:
                    raw_fund_line = lines[j - 1].strip()
                    fund_name = fund_status_pattern.sub("", raw_fund_line).strip()
                    if "criteria threshold" in fund_name.lower(): continue

                    fund_metrics = []
                    for k in range(j, j + 14):
                        if k >= len(lines): break
                        line = lines[k].strip()
                        match = re.match(r"(.+?)\s+(Pass|Review)\s*[-–]?\s*(.*)", line)
                        metric_name, status, reason = match.groups() if match else (line.split(" ", 1)[0], "N/A", "")
                        fund_metrics.append({"Metric": metric_name.strip(), "Status": status.strip(), "Reason": reason.strip()})
                    fund_blocks.append({"Fund Name": fund_name, "Metrics": fund_metrics})
        st.session_state["fund_blocks"] = fund_blocks

        # === IPS Evaluation ===
        def map_metric_names(fund_type):
            return [
                "Manager Tenure",
                "R² (3Yr)" if fund_type == "Passive" else "Excess Performance (3Yr)",
                "Return Rank (3Yr)",
                "Sharpe Ratio Rank (3Yr)",
                "Tracking Error Rank (3Yr)" if fund_type == "Passive" else "Sortino Ratio Rank (3Yr)",
                "R² (5Yr)" if fund_type == "Passive" else "Excess Performance (5Yr)",
                "Return Rank (5Yr)",
                "Sharpe Ratio Rank (5Yr)",
                "Tracking Error Rank (5Yr)" if fund_type == "Passive" else "Sortino Ratio Rank (5Yr)",
                "Expense Ratio Rank",
                "Investment Style"
            ]

        ips_results = []
        ips_criteria = [
            "Manager Tenure ≥ 3 years",
            "3-Year Performance > Benchmark / R² > 95%",
            "3-Year Performance > 50% of Peers",
            "3-Year Sharpe Ratio > 50% of Peers",
            "3-Year Sortino Ratio > 50% of Peers / Tracking Error < 90%",
            "5-Year Performance > Benchmark / R² > 95%",
            "5-Year Performance > 50% of Peers",
            "5-Year Sharpe Ratio > 50% of Peers",
            "5-Year Sortino Ratio > 50% of Peers / Tracking Error < 90%",
            "Expense Ratio < 50% of Peers",
            "Investment Style aligns with objectives"
        ]

        for block in fund_blocks:
            fund_name = block["Fund Name"]
            fund_type = "Passive" if "bitcoin" in fund_name.lower() else "Active"
            expected_metrics = map_metric_names(fund_type)
            metric_lookup = {m["Metric"]: m["Status"] for m in block["Metrics"]}
            results = []
            for i, label in enumerate(expected_metrics):
                status = metric_lookup.get(label, "Review")
                result = "Pass" if (i == 10 or status == "Pass") else "Fail"
                results.append({"Metric": ips_criteria[i], "Status": status})
            fail_count = sum(1 for r in results if r["Status"] != "Pass" and r["Metric"] != ips_criteria[10])
            overall_status = "Passed IPS Screen" if fail_count <= 4 else "Informal Watch (IW)" if fail_count == 5 else "Formal Watch (FW)"
            ips_results.append({
                "Fund Name": fund_name,
                "Fund Type": fund_type,
                "IPS Metrics": results,
                "Overall IPS Status": overall_status
            })
        st.session_state["step8_results"] = ips_results

        # === Factsheets ===
        factsheets = []
        perf_data = st.session_state["fund_blocks"]
        match_data = [{"Fund Scorecard Name": b["Fund Name"], "Ticker": "N/A"} for b in perf_data]
        factsheet_start = toc_pages["Fund Factsheets"]

        for i in range(factsheet_start - 1, len(pdf.pages)):
            page = pdf.pages[i]
            words = page.extract_words(use_text_flow=True)
            top_line = " ".join(w["text"] for w in words if w["top"] < 100)
            if "Benchmark:" not in top_line or "Expense Ratio:" not in top_line:
                continue

            ticker_match = re.search(r"\b([A-Z]{5})\b", top_line)
            ticker = ticker_match.group(1) if ticker_match else ""
            name_raw = top_line.split(ticker)[0].strip() if ticker else ""

            best_score = 0
            matched_name = ""
            for m in match_data:
                score = fuzz.token_sort_ratio(f"{name_raw} {ticker}", f"{m['Fund Scorecard Name']} {m['Ticker']}")
                if score > best_score:
                    best_score = score
                    matched_name = m["Fund Scorecard Name"]

            def get_val(label, text, stop=None):
                try:
                    start = text.index(label) + len(label)
                    segment = text[start:]
                    if stop and stop in segment:
                        return segment[:segment.index(stop)].strip()
                    return segment.split()[0]
                except Exception:
                    return ""

            factsheets.append({
                "Page #": i + 1,
                "Parsed Fund Name": name_raw,
                "Parsed Ticker": ticker,
                "Matched Fund Name": matched_name,
                "Matched Ticker": ticker,
                "Benchmark": get_val("Benchmark:", top_line, "Category:"),
                "Category": get_val("Category:", top_line, "Net Assets:"),
                "Net Assets": get_val("Net Assets:", top_line, "Manager Name:"),
                "Manager Name": get_val("Manager Name:", top_line, "Avg. Market Cap:"),
                "Avg. Market Cap": get_val("Avg. Market Cap:", top_line, "Expense Ratio:"),
                "Expense Ratio": get_val("Expense Ratio:", top_line),
                "Match Score": best_score,
                "Matched": "✅" if best_score > 20 else "❌"
            })
        st.session_state["fund_factsheets_data"] = factsheets
