import streamlit as st
import pdfplumber
import re

def extract_date_and_info(first_page_text):
    date_match = re.search(r"(3/31|6/20|9/30|12/31)/20\d{2}", first_page_text)
    quarter = {
        "3/31": "Q1",
        "6/20": "Q2",
        "9/30": "Q3",
        "12/31": "Q4"
    }.get(date_match.group(1)) if date_match else "Unknown"

    total_options = re.search(r"Total Options:\s*(\d+)", first_page_text)
    total_options_count = int(total_options.group(1)) if total_options else 0

    prepared_for = re.search(r"Prepared For:\s*\n(.+)", first_page_text)
    client_name = prepared_for.group(1).strip() if prepared_for else "Unknown"

    prepared_by = re.search(r"Prepared By:\s*\n(.+)", first_page_text)
    prepared_by_name = prepared_by.group(1).strip() if prepared_by else "Unknown"

    return quarter, total_options_count, client_name, prepared_by_name

def get_section_pages(toc_text):
    def find_page(keyword):
        for line in toc_text.split("\n"):
            if keyword in line:
                match = re.search(r"(\d+)$", line.strip())
                return int(match.group(1)) if match else None
        return None

    performance_page = find_page("Fund Performance: Current vs. Proposed Comparison")
    scorecard_page = find_page("Fund Scorecard")
    return performance_page, scorecard_page

def clean_scorecard_funds(scorecard_lines):
    funds = []
    i = 0
    while i < len(scorecard_lines):
        line = scorecard_lines[i]
        if "Manager Tenure" in line:
            if i > 0:
                name = scorecard_lines[i - 1].strip()
                name = re.sub(r"Fund Meets Watchlist Criteria\.", "", name)
                name = re.sub(r"Fund has been placed on watchlist.*", "", name)
                if (
                    name and
                    "criteria threshold" not in name.lower() and
                    "style" not in name.lower() and
                    "asset loading" not in name.lower() and
                    not name.lower().startswith("fund facts")
                ):
                    funds.append(name.strip())
            i += 14
        else:
            i += 1
    return funds

def extract_performance_data(perf_lines, fund_names):
    results = []

    for idx in range(1, len(perf_lines) - 1):
        raw_fund_line = perf_lines[idx]
        fund_line = raw_fund_line.strip()
        raw_cat_line = perf_lines[idx - 1]
        cat_line = raw_cat_line.strip()

        match = re.match(r"^(.*?)([A-Z]{5})\s*$", fund_line)
        if not match:
            continue

        fund_name = match.group(1).strip()
        ticker = match.group(2).strip()

        fund_indent = len(raw_fund_line) - len(raw_fund_line.lstrip())
        cat_indent = len(raw_cat_line) - len(raw_cat_line.lstrip())
        category = cat_line if cat_indent < fund_indent and not any(char.isdigit() for char in cat_line) else "Unknown"

        raw_benchmark = perf_lines[idx + 1].strip() if idx + 1 < len(perf_lines) else ""
        benchmark = raw_benchmark if raw_benchmark.lower().endswith("index") else "Unknown"

        if any(fund_name.lower().startswith(f.lower().split()[0]) for f in fund_names):
            results.append({
                "Fund Name": fund_name,
                "Ticker": ticker,
                "Category": category,
                "Benchmark": benchmark
            })

    return results

def run():
    st.set_page_config(page_title="All Steps Combined", layout="wide")
    st.title("IPS Investment Criteria Evaluator (Full Pipeline)")

    uploaded_file = st.file_uploader("Upload MPI PDF", type=["pdf"])
    if not uploaded_file:
        return

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            first_page_text = pdf.pages[0].extract_text()
            quarter, total_options, client_name, prepared_by = extract_date_and_info(first_page_text)

            st.markdown(f"**Time Period Detected:** {quarter}")
            st.markdown(f"**Total Options:** {total_options}")
            st.markdown(f"**Prepared For:** {client_name}")
            st.markdown(f"**Prepared By:** {prepared_by}")

            toc_text = pdf.pages[1].extract_text()
            perf_page, scorecard_page = get_section_pages(toc_text)
            if not perf_page or not scorecard_page:
                st.error("❌ Could not detect required sections from Table of Contents.")
                return

            scorecard_lines = []
            for page in pdf.pages[scorecard_page - 1:]:
                text = page.extract_text()
                if not text or "Style Box Analysis" in text:
                    break
                scorecard_lines.extend(text.split("\n"))
            fund_names = clean_scorecard_funds(scorecard_lines)

            perf_lines = []
            for page in pdf.pages[perf_page - 1:]:
                text = page.extract_text()
                if not text or "Fund Factsheets" in text:
                    break
                perf_lines.extend(text.split("\n"))

            performance_results = extract_performance_data(perf_lines, fund_names)

            st.subheader("Final Extracted Fund Performance Info")
            if not performance_results:
                st.warning("No matching funds found.")
            else:
                for r in performance_results:
                    st.markdown(f"### ✅ {r['Fund Name']}")
                    st.markdown(f"- **Ticker:** {r['Ticker']}")
                    st.markdown(f"- **Category:** {r['Category']}")
                    st.markdown(f"- **Benchmark:** {r['Benchmark']}")
                    st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
