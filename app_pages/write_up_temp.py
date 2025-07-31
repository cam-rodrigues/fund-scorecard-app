import re
import streamlit as st
import pdfplumber
from calendar import month_name
import pandas as pd
from rapidfuzz import fuzz
from pptx import Presentation
from pptx.util import Inches
from io import BytesIO

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    """
    Extracts and labels the report date from the provided text.
    Returns a formatted string for quarter-end dates or a human-readable date.
    """
    # Regex to match dates in MM/DD/YYYY format
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    
    for month, day, year in dates:
        month, day = int(month), int(day)
        
        # Check if the date is a quarter-end date
        if (month, day) in [(3, 31), (6, 30), (9, 30), (12, 31)]:
            quarter_map = {(3, 31): "1st", (6, 30): "2nd", (9, 30): "3rd", (12, 31): "4th"}
            return f"{quarter_map[(month, day)]} QTR, {year}"
        
        # Fallback: return a human-readable date
        return f"As of {month_name[month]} {day}, {year}"

    # If no date is found, return None
    return None

# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    """
    Processes the text from Page 1 of the PDF to extract and store metadata 
    such as report date, total options, prepared for/by information.
    """
    # Extract and store report date
    report_date = extract_report_date(text)
    if report_date:
        st.session_state['report_date'] = report_date
        st.success(f"Report Date: {report_date}")
    else:
        st.error("Could not detect report date on page 1.")
    
    # Extract and store the total options
    total_options_match = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state['total_options'] = int(total_options_match.group(1)) if total_options_match else None

    # Extract and store "Prepared For" value
    prepared_for_match = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state['prepared_for'] = prepared_for_match.group(1).strip() if prepared_for_match else None

    # Extract and store "Prepared By" value, defaulting to "Procyon Partners, LLC"
    prepared_by_match = re.search(r"Prepared By:\s*(.*)", text or "")
    prepared_by = prepared_by_match.group(1).strip() if prepared_by_match else ""
    if not prepared_by or "mpi stylus" in prepared_by.lower():
        prepared_by = "Procyon Partners, LLC"
    st.session_state['prepared_by'] = prepared_by

    # Display extracted metadata
    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: {prepared_by}")
# ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
#=== Step 2: Table of Contents Extraction ===
def process_toc(text):
    """
    Extracts the page numbers for the different sections of the Table of Contents (TOC) from the provided text.
    Stores the extracted page numbers in session state for future reference.
    """
    # Define the regex patterns to extract page numbers for each section
    sections = {
        "Fund Performance Current vs Proposed Comparison": r"Fund Performance[^\d]*(\d{1,3})",
        "Fund Scorecard": r"Fund Scorecard\s+(\d{1,3})",
        "Fund Factsheets": r"Fund Factsheets\s+(\d{1,3})",
        "Fund Performance: Calendar Year": r"Fund Performance: Calendar Year\s+(\d{1,3})",
        "Risk Analysis: MPT Statistics (3Yr)": r"Risk Analysis: MPT Statistics \(3Yr\)\s+(\d{1,3})",
        "Risk Analysis: MPT Statistics (5Yr)": r"Risk Analysis: MPT Statistics \(5Yr\)\s+(\d{1,3})"
    }

    # Extract page numbers using regex
    page_numbers = {
        section: (int(re.search(pattern, text or "").group(1)) if re.search(pattern, text) else None)
        for section, pattern in sections.items()
    }

    # Display the extracted pages in the UI
    st.subheader("Table of Contents Pages")
    for section, page in page_numbers.items():
        st.write(f"- {section}: {page}")

    # Store extracted page numbers in session state for future reference
    for section, page in page_numbers.items():
        st.session_state[f"{section.lower().replace(' ', '_')}_page"] = page

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 3 ===
def step3_process_scorecard(pdf, start_page, declared_total):
    """
    Processes the scorecard section of the PDF starting from the specified page and extracts
    fund name, metrics, and their status (Pass or Review).
    """
    # Gather all pages from the start page and extract text
    pages = []
    for p in pdf.pages[start_page - 1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break

    # Split the collected text into lines
    lines = "\n".join(pages).splitlines()

    # Find the start of the metrics section after "Criteria Threshold"
    idx = next((i for i, l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx + 1:]

    fund_blocks = []
    name = None
    metrics = []

    # Loop through lines to extract metric info (Metric, Pass/Review, Info)
    for i, line in enumerate(lines):
        match = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
        if not match:
            continue

        metric, status, info = match.groups()

        # When encountering the "Manager Tenure" metric, save the previous fund block
        if metric == "Manager Tenure":
            if name and metrics:
                fund_blocks.append({"Fund Name": name, "Metrics": metrics})

            # Find the fund name from the previous non-blank line
            prev = ""
            for j in range(i - 1, -1, -1):
                if lines[j].strip():
                    prev = lines[j].strip()
                    break
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            metrics = []

        # Append the metric and its status to the fund's metrics list
        if name:
            metrics.append({"Metric": metric, "Status": status, "Info": info})

    # Ensure the last fund block is added
    if name and metrics:
        fund_blocks.append({"Fund Name": name, "Metrics": metrics})

    # Save extracted data to session state
    st.session_state["fund_blocks"] = fund_blocks

    # Display the fund blocks and metrics
    st.subheader("Step 3.5: Key Details per Metric")
    for block in fund_blocks:
        st.markdown(f"### {block['Fund Name']}")
        for metric in block["Metrics"]:
            st.write(f"- **{metric['Metric']}** ({metric['Status']}): {metric['Info'].strip()}")

    # Display the investment option count comparison
    st.subheader("Step 3.6: Investment Option Count")
    count = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{count}**")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Expected {declared_total}, found {count}.")


#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 4: IPS Screening ===
def step4_ips_screen():
    # Check if 'fund_blocks' exist in session state, indicating Step 3 has run
    if "fund_blocks" not in st.session_state:
        st.error("❌ 'fund_blocks' not found. Please run Step 3 to process scorecard data first.")
        return

    IPS = [
        "Manager Tenure",
        "Excess Performance (3Yr)",
        "R-Squared (3Yr)",
        "Peer Return Rank (3Yr)",
        "Sharpe Ratio Rank (3Yr)",
        "Sortino Ratio Rank (3Yr)",
        "Tracking Error Rank (3Yr)",
        "Excess Performance (5Yr)",
        "R-Squared (5Yr)",
        "Peer Return Rank (5Yr)",
        "Sharpe Ratio Rank (5Yr)",
        "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (5Yr)",
        "Expense Ratio Rank"
    ]
    st.subheader("Step 4: IPS Investment Criteria Screening")

    for b in st.session_state["fund_blocks"]:
        name = b["Fund Name"]
        is_passive = "bitcoin" in name.lower()  # Assuming funds with 'bitcoin' are passive; adjust as needed
        statuses, reasons = {}, {}

        # Extract the scorecard metrics and convert them to IPS criteria
        scorecard_metrics = {
            1: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Manager Tenure"), "Fail"),
            2: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Excess Performance"), "Fail"),
            3: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Excess Performance (5Yr)"), "Fail"),
            4: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Peer Return Rank (3Yr)"), "Fail"),
            5: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Peer Return Rank (5Yr)"), "Fail"),
            6: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Expense Ratio Rank"), "Fail"),
            7: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Sharpe Ratio Rank (3Yr)"), "Fail"),
            8: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Sharpe Ratio Rank (5Yr)"), "Fail"),
            9: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "R-Squared (3Yr)"), "Fail"),
            10: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "R-Squared (5Yr)"), "Fail"),
            11: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Sortino Ratio Rank (3Yr)"), "Fail"),
            12: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Sortino Ratio Rank (5Yr)"), "Fail"),
            13: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Tracking Error Rank (3Yr)"), "Fail"),
            14: next((m["Status"] for m in b["Metrics"] if m["Metric"] == "Tracking Error Rank (5Yr)"), "Fail"),
        }

        # Conversion logic for scorecard metrics to IPS criteria
        ips_criteria = convert_scorecard_to_ips(scorecard_metrics, fund_type="passive" if is_passive else "active")

        # Map the converted IPS criteria to statuses
        for idx, criterion in enumerate(ips_criteria):
            statuses[IPS[idx]] = "✅" if ips_criteria[criterion] == "Pass" else "❌"
            reasons[IPS[idx]] = f"{ips_criteria[criterion]}"

        # Display the fund's IPS status
        st.markdown(f"### {name} ({'Passive' if is_passive else 'Active'})")
        st.write(f"**Overall IPS Status:** {statuses['Manager Tenure']} ({sum(1 for v in statuses.values() if v == '✅')} passes)")

        for criterion, status in statuses.items():
            st.write(f"- {status} **{criterion}**: {reasons.get(criterion, '—')}")


#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 5: Fund Performance Section Extraction (with fallback) ===
def step5_process_performance(pdf, start_page, fund_names):
    # figure out where the section ends
    end_page = st.session_state.get("factsheets_page") or (len(pdf.pages) + 1)

    # gather all lines and the raw text
    all_lines = []
    perf_text = ""
    for p in pdf.pages[start_page-1 : end_page-1]:
        txt = p.extract_text() or ""
        perf_text += txt + "\n"
        all_lines.extend(txt.splitlines())

    # first pass: normalized line → ticker (1–5 uppercase letters)
    mapping = {}
    for ln in all_lines:
        m = re.match(r"(.+?)\s+([A-Z]{1,5})$", ln.strip())
        if not m:
            continue
        raw_name, ticker = m.groups()
        norm = re.sub(r'[^A-Za-z0-9 ]+', '', raw_name).strip().lower()
        mapping[norm] = ticker

    # try matching each fund by normalized prefix
    tickers = {}
    for name in fund_names:
        norm_expected = re.sub(r'[^A-Za-z0-9 ]+', '', name).strip().lower()
        found = next(
            (t for raw, t in mapping.items() if raw.startswith(norm_expected)),
            None
        )
        tickers[name] = found

    # if too few, fallback to ordered scrape of every 1–5 letter code
    total = len(fund_names)
    found_count = sum(1 for t in tickers.values() if t)
    if found_count < total:
        all_tks = re.findall(r'\b([A-Z]{1,5})\b', perf_text)
        seen = []
        for tk in all_tks:
            if tk not in seen:
                seen.append(tk)
        tickers = {
            name: (seen[i] if i < len(seen) else None)
            for i, name in enumerate(fund_names)
        }

    # store & display
    st.session_state["tickers"] = tickers
    st.subheader("Step 5: Extracted Tickers")
    for n, t in tickers.items():
        st.write(f"- {n}: {t or '❌ not found'}")

    # validation
    st.subheader("Step 5.5: Ticker Count Validation")
    found_count = sum(1 for t in tickers.values() if t)
    st.write(f"- Expected tickers: **{total}**")
    st.write(f"- Found tickers:    **{found_count}**")
    if found_count == total:
        st.success("✅ All tickers found.")
    else:
        st.error(f"❌ Missing {total - found_count} ticker(s).")

    st.session_state["fund_performance_data"] = [
        {"Fund Scorecard Name": name, "Ticker": ticker}
        for name, ticker in tickers.items()
    ]


def extract_field(text: str, label: str, stop_at: str = None) -> str:
    """
    Extracts the substring immediately following `label` up to `stop_at` (if provided),
    else returns the first whitespace-delimited token.
    """
    try:
        start = text.index(label) + len(label)
        rest  = text[start:]
        if stop_at and stop_at in rest:
            return rest[:rest.index(stop_at)].strip()
        return rest.split()[0].strip()
    except ValueError:
        return ""

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 6: Fund Factsheets ===
def step6_process_factsheets(pdf, fund_names):
    st.subheader("Step 6: Fund Factsheets Section")
    factsheet_start = st.session_state.get("factsheets_page")
    total_declared = st.session_state.get("total_options")
    performance_data = [
        {"Fund Scorecard Name": name, "Ticker": ticker}
        for name, ticker in st.session_state.get("tickers", {}).items()
    ]

    if not factsheet_start:
        st.error("❌ 'Fund Factsheets' page number not found in TOC.")
        return

    matched_factsheets = []
    # Iterate pages from factsheet_start to end
    for i in range(factsheet_start - 1, len(pdf.pages)):
        page = pdf.pages[i]
        words = page.extract_words(use_text_flow=True)
        header_words = [w['text'] for w in words if w['top'] < 100]
        first_line = " ".join(header_words).strip()

        if not first_line or "Benchmark:" not in first_line or "Expense Ratio:" not in first_line:
            continue

        ticker_match = re.search(r"\b([A-Z]{5})\b", first_line)
        ticker = ticker_match.group(1) if ticker_match else ""
        fund_name_raw = first_line.split(ticker)[0].strip() if ticker else first_line

        best_score = 0
        matched_name = matched_ticker = ""
        for item in performance_data:
            ref = f"{item['Fund Scorecard Name']} {item['Ticker']}".strip()
            score = fuzz.token_sort_ratio(f"{fund_name_raw} {ticker}".lower(), ref.lower())
            if score > best_score:
                best_score, matched_name, matched_ticker = score, item['Fund Scorecard Name'], item['Ticker']

        def extract_field(label, text, stop=None):
            try:
                start = text.index(label) + len(label)
                rest = text[start:]
                if stop and stop in rest:
                    return rest[:rest.index(stop)].strip()
                return rest.split()[0]
            except Exception:
                return ""

        benchmark = extract_field("Benchmark:", first_line, "Category:")
        category  = extract_field("Category:", first_line, "Net Assets:")
        net_assets= extract_field("Net Assets:", first_line, "Manager Name:")
        manager   = extract_field("Manager Name:", first_line, "Avg. Market Cap:")
        avg_cap   = extract_field("Avg. Market Cap:", first_line, "Expense Ratio:")
        expense   = extract_field("Expense Ratio:", first_line)

        matched_factsheets.append({
            "Page #": i + 1,
            "Parsed Fund Name": fund_name_raw,
            "Parsed Ticker": ticker,
            "Matched Fund Name": matched_name,
            "Matched Ticker": matched_ticker,
            "Benchmark": benchmark,
            "Category": category,
            "Net Assets": net_assets,
            "Manager Name": manager,
            "Avg. Market Cap": avg_cap,
            "Expense Ratio": expense,
            "Match Score": best_score,
            "Matched": "✅" if best_score > 20 else "❌"
        })

    df_facts = pd.DataFrame(matched_factsheets)
    st.session_state['fund_factsheets_data'] = matched_factsheets

    display_df = df_facts[[
        "Matched Fund Name", "Matched Ticker", "Benchmark", "Category",
        "Net Assets", "Manager Name", "Avg. Market Cap", "Expense Ratio", "Matched"
    ]].rename(columns={"Matched Fund Name": "Fund Name", "Matched Ticker": "Ticker"})

    st.dataframe(display_df, use_container_width=True)

    matched_count = sum(1 for r in matched_factsheets if r["Matched"] == "✅")
    if not st.session_state.get("suppress_matching_confirmation", False):
        st.write(f"Matched {matched_count} of {len(matched_factsheets)} factsheet pages.")
        if matched_count == total_declared:
            st.success(f"All {matched_count} funds matched the declared Total Options from Page 1.")
        else:
            st.error(f"Mismatch: Page 1 declared {total_declared}, but only matched {matched_count}.")

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 7: QTD / 1Yr / 3Yr / 5Yr / 10Yr / Net Expense Ratio & Bench QTD ===
def step7_extract_returns(pdf):
    import re
    import pandas as pd
    import streamlit as st
    from rapidfuzz import fuzz

    st.subheader("Step 7: QTD / 1Yr / 3Yr / 5Yr / 10Yr / Net Expense & Benchmark QTD")

    # 1) Where to scan
    perf_page = st.session_state.get("performance_page")
    end_page  = st.session_state.get("calendar_year_page") or (len(pdf.pages) + 1)
    perf_data = st.session_state.get("fund_performance_data", [])
    if perf_page is None or not perf_data:
        st.error("❌ Run Step 5 first to populate performance data.")
        return

    # 2) Prep output slots
    fields = ["QTD", "1Yr", "3Yr", "5Yr", "10Yr", "Net Expense Ratio", "Bench QTD", "Bench 3Yr", "Bench 5Yr"]
    for itm in perf_data:
        for f in fields:
            itm.setdefault(f, None)

    # 3) Gather every nonblank line in the Performance section
    lines = []
    for pnum in range(perf_page - 1, end_page - 1):
        txt = pdf.pages[pnum].extract_text() or ""
        lines += [ln.strip() for ln in txt.splitlines() if ln.strip()]

    # 4) Regex to pull decimal tokens (with optional % and parentheses)
    num_rx = re.compile(r"\(?-?\d+\.\d+%?\)?")

    matched = 0
    for item in perf_data:
        name = item["Fund Scorecard Name"]
        tk   = item["Ticker"].upper().strip()

        # a) Exact-ticker match
        idx = next(
            (i for i, ln in enumerate(lines)
             if re.search(rf"\b{re.escape(tk)}\b", ln)),
            None
        )
        # b) Fuzzy-name fallback
        if idx is None:
            scores = [(i, fuzz.token_sort_ratio(name.lower(), ln.lower()))
                      for i, ln in enumerate(lines)]
            best_i, best_score = max(scores, key=lambda x: x[1])
            if best_score > 60:
                idx = best_i
            else:
                st.warning(f"⚠️ {name} ({tk}): no match found.")
                continue

        # c) Pull fund numbers from line above (and two above if needed)
        raw = num_rx.findall(lines[idx - 1]) if idx >= 1 else []
        if len(raw) < 8 and idx >= 2:
            raw = num_rx.findall(lines[idx - 2]) + raw
        clean = [n.strip("()%").rstrip("%") for n in raw]
        if len(clean) < 8:
            clean += [None] * (8 - len(clean))

        # d) Map fund returns & net expense
        item["QTD"]               = clean[0]
        item["1Yr"]               = clean[2]
        item["3Yr"]               = clean[3]
        item["5Yr"]               = clean[4]
        item["10Yr"]              = clean[5]
        item["Net Expense Ratio"] = clean[-2]

        # e) Pull benchmark QTD, 3Yr, and 5Yr from the very next line (or one more down)
        bench_raw = []
        if idx + 1 < len(lines):
            bench_raw = num_rx.findall(lines[idx + 1])
        if len(bench_raw) < 1 and idx + 2 < len(lines):
            bench_raw = num_rx.findall(lines[idx + 2])
        bench_clean = [n.strip("()%").rstrip("%") for n in bench_raw]

        item["Bench QTD"] = bench_clean[0] if bench_clean else None
        item["Bench 3Yr"] = bench_clean[3] if len(bench_clean) > 3 else None
        item["Bench 5Yr"] = bench_clean[4] if len(bench_clean) > 4 else None

        matched += 1

    # 5) Save & display
    st.session_state["fund_performance_data"] = perf_data
    df = pd.DataFrame(perf_data)

    st.success(f"✅ Matched {matched} fund(s) with return data.")
    for itm in perf_data:
        missing = [f for f in fields if not itm.get(f)]
        if missing:
            st.warning(f"⚠️ Incomplete for {itm['Fund Scorecard Name']} ({itm['Ticker']}): missing {', '.join(missing)}")

    st.dataframe(
        df[["Fund Scorecard Name", "Ticker"] + fields],
        use_container_width=True
    )

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 8 Calendar Year Returns (funds + benchmarks) ===
def step8_calendar_returns(pdf):
    import re, streamlit as st, pandas as pd

    st.subheader("Step 8: Calendar Year Returns")

    # 1) Figure out section bounds
    cy_page  = st.session_state.get("calendar_year_page")
    end_page = st.session_state.get("r3yr_page", len(pdf.pages) + 1)
    if cy_page is None:
        st.error("❌ 'Fund Performance: Calendar Year' not found in TOC.")
        return

    # 2) Pull every line from that section
    all_lines = []
    for p in pdf.pages[cy_page-1 : end_page-1]:
        all_lines.extend((p.extract_text() or "").splitlines())

    # 3) Identify header & years
    header = next((ln for ln in all_lines if "Ticker" in ln and re.search(r"20\d{2}", ln)), None)
    if not header:
        st.error("❌ Couldn’t find header row with 'Ticker' + year.")
        return
    years = re.findall(r"\b20\d{2}\b", header)
    num_rx = re.compile(r"-?\d+\.\d+%?")

    # — A) Funds themselves —
    fund_map     = st.session_state.get("tickers", {})
    fund_records = []
    for name, tk in fund_map.items():
        ticker = (tk or "").upper()
        idx    = next((i for i, ln in enumerate(all_lines) if ticker in ln.split()), None)
        raw    = num_rx.findall(all_lines[idx-1]) if idx not in (None, 0) else []
        vals   = raw[:len(years)] + [None] * (len(years) - len(raw))
        rec    = {"Name": name, "Ticker": ticker}
        rec.update({years[i]: vals[i] for i in range(len(years))})
        fund_records.append(rec)

    df_fund = pd.DataFrame(fund_records)
    if not df_fund.empty:
        st.markdown("**Fund Calendar‑Year Returns**")
        st.dataframe(df_fund[["Name", "Ticker"] + years], use_container_width=True)
        st.session_state["step8_returns"] = fund_records

    # — B) Benchmarks matched back to each fund’s ticker —
    facts         = st.session_state.get("fund_factsheets_data", [])
    bench_records = []
    for f in facts:
        bench_name = f.get("Benchmark", "").strip()
        fund_tkr   = f.get("Matched Ticker", "")
        if not bench_name:
            continue

        # find the first line containing the benchmark name
        idx = next((i for i, ln in enumerate(all_lines) if bench_name in ln), None)
        if idx is None:
            continue
        raw  = num_rx.findall(all_lines[idx])
        vals = raw[:len(years)] + [None] * (len(years) - len(raw))
        rec  = {"Name": bench_name, "Ticker": fund_tkr}
        rec.update({years[i]: vals[i] for i in range(len(years))})
        bench_records.append(rec)

    df_bench = pd.DataFrame(bench_records)
    if not df_bench.empty:
        st.markdown("**Benchmark Calendar‑Year Returns**")
        st.dataframe(df_bench[["Name", "Ticker"] + years], use_container_width=True)
        st.session_state["benchmark_calendar_year_returns"] = bench_records
    else:
        st.warning("No benchmark returns extracted.")

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 9: 3‑Yr Risk Analysis – Match & Extract MPT Stats (hidden matching) ===
def step9_risk_analysis_3yr(pdf):
    import re, streamlit as st, pandas as pd
    from rapidfuzz import fuzz

    st.subheader("Step 9: Risk Analysis (3Yr) – MPT Statistics")

    # 1) Get your fund→ticker map
    fund_map = st.session_state.get("tickers", {})
    if not fund_map:
        st.error("❌ No ticker mapping found. Run Step 5 first.")
        return

    # 2) Locate the “Risk Analysis: MPT Statistics (3Yr)” page
    start_page = st.session_state.get("r3yr_page")
    if not start_page:
        st.error("❌ ‘Risk Analysis: MPT Statistics (3Yr)’ page not found; run Step 2 first.")
        return

    # 3) Scan forward until you’ve seen each ticker (no display)
    locs = {}
    for pnum in range(start_page, len(pdf.pages) + 1):
        lines = (pdf.pages[pnum-1].extract_text() or "").splitlines()
        for li, ln in enumerate(lines):
            tokens = ln.split()
            for fname, tk in fund_map.items():
                if fname in locs: 
                    continue
                if tk.upper() in tokens:
                    locs[fname] = {"page": pnum, "line": li}
        if len(locs) == len(fund_map):
            break

    # 4) Extract the first four numeric MPT stats from that same line
    num_rx = re.compile(r"-?\d+\.\d+")
    results = []
    for name, info in locs.items():
        page = pdf.pages[info["page"]-1]
        lines = (page.extract_text() or "").splitlines()
        line = lines[info["line"]]
        nums = num_rx.findall(line)
        nums += [None] * (4 - len(nums))
        alpha, beta, up, down = nums[:4]
        results.append({
            "Fund Name":               name,
            "Ticker":                  fund_map[name].upper(),
            "3 Year Alpha":            alpha,
            "3 Year Beta":             beta,
            "3 Year Upside Capture":   up,
            "3 Year Downside Capture": down
        })

    # 5) Display final table only
    st.session_state["step9_mpt_stats"] = results
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)


#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 10: Risk Analysis (5Yr) – Match & Extract MPT Statistics ===
def step10_risk_analysis_5yr(pdf):
    import re, streamlit as st, pandas as pd

    st.subheader("Step 10: Risk Analysis (5Yr) – MPT Statistics")

    # 1) Your fund→ticker map from Step 5
    fund_map = st.session_state.get("tickers", {})
    if not fund_map:
        st.error("❌ No ticker mapping found. Run Step 5 first.")
        return

    # 2) Locate the “Risk Analysis: MPT Statistics (5Yr)” section
    section_page = next(
        (i for i, pg in enumerate(pdf.pages, start=1)
         if "Risk Analysis: MPT Statistics (5Yr)" in (pg.extract_text() or "")),
        None
    )
    if section_page is None:
        st.error("❌ Could not find ‘Risk Analysis: MPT Statistics (5Yr)’ section.")
        return

    # 3) Under‑the‑hood: scan pages until each ticker is located
    locs = {}
    total = len(fund_map)
    for pnum in range(section_page, len(pdf.pages) + 1):
        lines = (pdf.pages[pnum-1].extract_text() or "").splitlines()
        for li, ln in enumerate(lines):
            tokens = ln.split()
            for name, tk in fund_map.items():
                if name in locs:
                    continue
                if tk.upper() in tokens:
                    locs[name] = {"page": pnum, "line": li}
        if len(locs) == total:
            break

    # 4) Wrap‑aware extraction of the first four floats after each ticker line
    num_rx = re.compile(r"-?\d+\.\d+")
    results = []
    for name, tk in fund_map.items():
        info = locs.get(name)
        vals = [None] * 4
        if info:
            page = pdf.pages[info["page"] - 1]
            text_lines = (page.extract_text() or "").splitlines()
            idx = info["line"]
            nums = []
            # look on the line of the ticker and up to the next 2 lines
            for j in range(idx, min(idx + 3, len(text_lines))):
                nums += num_rx.findall(text_lines[j])
                if len(nums) >= 4:
                    break
            nums += [None] * (4 - len(nums))
            vals = nums[:4]
        else:
            st.warning(f"⚠️ {name} ({tk.upper()}): not found after page {section_page}.")

        alpha5, beta5, up5, down5 = vals
        results.append({
            "Fund Name":               name,
            "Ticker":                  tk.upper(),
            "5 Year Alpha":            alpha5,
            "5 Year Beta":             beta5,
            "5 Year Upside Capture":   up5,
            "5 Year Downside Capture": down5,
        })

    # 5) Save & display only the consolidated table
    st.session_state["step10_mpt_stats"] = results
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)


#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 11: Combined MPT Statistics Summary ===
def step11_create_summary(pdf=None):
    import pandas as pd
    import streamlit as st

    st.subheader("Step 11: MPT Statistics Summary")

    # 1) Load your 3‑Yr and 5‑Yr stats from session state
    mpt3 = st.session_state.get("step9_mpt_stats", [])
    mpt5 = st.session_state.get("step10_mpt_stats", [])
    if not mpt3 or not mpt5:
        st.error("❌ Missing MPT stats. Run Steps 9 & 10 first.")
        return

    # 2) Build DataFrames
    df3 = pd.DataFrame(mpt3)  # contains "3 Year Alpha", "3 Year Beta", etc.
    df5 = pd.DataFrame(mpt5)  # contains "5 Year Alpha", "5 Year Beta", etc.

    # 3) Merge on Fund Name & Ticker
    df = pd.merge(
        df3,
        df5,
        on=["Fund Name", "Ticker"],
        how="outer",
        suffixes=("_3yr", "_5yr")
    )

    # 4) Build the Investment Manager column
    df.insert(0, "Investment Manager", df["Fund Name"] + " (" + df["Ticker"] + ")")

    # 5) Select & order the columns
    df = df[[
        "Investment Manager",
        "3 Year Alpha",
        "5 Year Alpha",
        "3 Year Beta",
        "5 Year Beta",
        "3 Year Upside Capture",
        "3 Year Downside Capture",
        "5 Year Upside Capture",
        "5 Year Downside Capture"
    ]]

    # 6) Display
    st.session_state["step11_summary"] = df.to_dict("records")
    st.dataframe(df)

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 12: Extract “FUND FACTS” & Its Table Details in One Go ===
def step12_process_fund_facts(pdf):
    import re
    import streamlit as st
    import pandas as pd

    st.subheader("Step 12: Fund Facts")

    fs_start   = st.session_state.get("factsheets_page")
    factsheets = st.session_state.get("fund_factsheets_data", [])
    if not fs_start or not factsheets:
        st.error("❌ Run Step 6 first to populate your factsheet pages.")
        return

    # map factsheet pages to fund name & ticker
    page_map = {
        f["Page #"]: (f["Matched Fund Name"], f["Matched Ticker"])
        for f in factsheets
    }

    # the exact labels and the order you want them in the table
    labels = [
        "Manager Tenure Yrs.",
        "Expense Ratio",
        "Expense Ratio Rank",
        "Total Number of Holdings",
        "Turnover Ratio"
    ]

    records = []
    # scan each factsheet page
    for pnum in range(fs_start, len(pdf.pages) + 1):
        if pnum not in page_map:
            continue
        fund_name, ticker = page_map[pnum]
        lines = pdf.pages[pnum-1].extract_text().splitlines()

        for idx, line in enumerate(lines):
            if line.lstrip().upper().startswith("FUND FACTS"):
                # grab the next 8 lines (should contain your 5 labels)
                snippet = lines[idx+1 : idx+1+8]
                rec = {"Fund Name": fund_name, "Ticker": ticker}
                for lab in labels:
                    val = None
                    for ln in snippet:
                        norm = " ".join(ln.strip().split())
                        if norm.startswith(lab):
                            rest = norm[len(lab):].strip(" :\t")
                            m = re.match(r"(-?\d+\.\d+)", rest)
                            val = m.group(1) if m else (rest.split()[0] if rest else None)
                            break
                    rec[lab] = val
                records.append(rec)
                break  # move on to the next page once Fund Facts is processed

    if not records:
        st.warning("No Fund Facts tables found.")
        return

    # save & show
    st.session_state["step12_fund_facts_table"] = records
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# === Step 13: Extract Risk‑Adjusted Returns Metrics ===
def step13_process_risk_adjusted_returns(pdf):
    import re
    import streamlit as st
    import pandas as pd

    st.subheader("Step 13: Risk‑Adjusted Returns")

    fs_start   = st.session_state.get("factsheets_page")
    factsheets = st.session_state.get("fund_factsheets_data", [])
    if not fs_start or not factsheets:
        st.error("❌ Run Step 6 first to populate your factsheet pages.")
        return

    # map factsheet pages to fund name & ticker
    page_map = {
        f["Page #"]: (f["Matched Fund Name"], f["Matched Ticker"])
        for f in factsheets
    }

    # which metrics to pull
    metrics = ["Sharpe Ratio", "Information Ratio", "Sortino Ratio"]
    num_rx  = re.compile(r"-?\d+\.\d+")

    records = []
    for pnum in range(fs_start, len(pdf.pages) + 1):
        if pnum not in page_map:
            continue
        fund_name, ticker = page_map[pnum]
        lines = (pdf.pages[pnum-1].extract_text() or "").splitlines()

        # find the heading
        for idx, line in enumerate(lines):
            norm = " ".join(line.strip().split()).upper()
            if norm.startswith("RISK-ADJUSTED RETURNS"):
                snippet = lines[idx+1 : idx+1+6]  # grab next few lines
                rec = {"Fund Name": fund_name, "Ticker": ticker}

                for metric in metrics:
                    # find the snippet line for this metric
                    text_line = next(
                        ( " ".join(ln.strip().split())
                          for ln in snippet
                          if ln.strip().upper().startswith(metric.upper()) ),
                        None
                    ) or ""
                    # extract up to 4 numbers
                    nums = num_rx.findall(text_line)
                    nums += [None] * (4 - len(nums))

                    # assign into rec
                    rec[f"{metric} 1Yr"]  = nums[0]
                    rec[f"{metric} 3Yr"]  = nums[1]
                    rec[f"{metric} 5Yr"]  = nums[2]
                    rec[f"{metric} 10Yr"] = nums[3]

                records.append(rec)
                break  # done with this page

    if not records:
        st.warning("No 'RISK‑ADJUSTED RETURNS' tables found.")
        return

    # save & show
    st.session_state["step13_risk_adjusted_table"] = records
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)

#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# == Step 14: Peer Risk-Adjusted Return Rank ==
def step14_extract_peer_risk_adjusted_return_rank(pdf):
    import re
    import streamlit as st
    import pandas as pd

    st.subheader("Step 14: Peer Risk-Adjusted Return Rank")

    factsheets = st.session_state.get("fund_factsheets_data", [])
    if not factsheets:
        st.error("❌ Run Step 6 first to populate your factsheet pages.")
        return

    page_map = {
        f["Page #"]:(f["Matched Fund Name"], f["Matched Ticker"])
        for f in factsheets
    }

    metrics = ["Sharpe Ratio", "Information Ratio", "Sortino Ratio"]
    records = []

    for pnum, (fund, ticker) in page_map.items():
        page = pdf.pages[pnum-1]
        text = page.extract_text() or ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        # 1) locate the Risk-Adjusted Returns header
        try:
            risk_idx = next(i for i, ln in enumerate(lines)
                            if "RISK-ADJUSTED RETURNS" in ln.upper())
        except StopIteration:
            st.warning(f"⚠️ {fund} ({ticker}): Risk-Adjusted header not found.")
            continue

        # 2) find all “1 Yr 3 Yrs 5 Yrs 10 Yrs” lines after that
        header_idxs = [i for i, ln in enumerate(lines)
                       if re.match(r"1\s*Yr", ln)]
        peer_header_idxs = [i for i in header_idxs if i > risk_idx]

        if not peer_header_idxs:
            st.warning(f"⚠️ {fund} ({ticker}): peer header not found.")
            continue

        # take the *second* header occurrence (first is Risk-Adjusted, next is Peer)
        peer_hdr = peer_header_idxs[0] if len(peer_header_idxs)==1 else peer_header_idxs[1]

        rec = {"Fund Name": fund, "Ticker": ticker}

        # 3) read the three lines immediately below that header
        for offset, metric in enumerate(metrics, start=1):
            if peer_hdr + offset < len(lines):
                parts = lines[peer_hdr + offset].split()
                # parts[0:2] = metric name words, parts[2:6] = the four integer ranks
                vals = parts[2:6] if len(parts) >= 6 else []
            else:
                vals = []

            # fill into record (pad with None if missing)
            for idx, period in enumerate(["1Yr","3Yr","5Yr","10Yr"]):
                rec[f"{metric} {period}"] = vals[idx] if idx < len(vals) else None

            if len(vals) < 4:
                st.warning(f"⚠️ {fund} ({ticker}): only {len(vals)} peer values found for '{metric}'.")

        records.append(rec)

    if not records:
        st.warning("❌ No Peer Risk-Adjusted Return Rank data extracted.")
        return

    df = pd.DataFrame(records)
    st.session_state["step14_peer_rank_table"] = records
    st.dataframe(df, use_container_width=True)


#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Step 15: Single Fund Details ===
def step15_display_selected_fund():
    import pandas as pd
    import streamlit as st
    import re

    st.subheader("Step 15: Single Fund Details")
    facts = st.session_state.get("fund_factsheets_data", [])
    if not facts:
        st.info("Run Steps 1–14 to populate data before viewing fund details.")
        return

    # Select a fund
    fund_names = [f["Matched Fund Name"] for f in facts]
    selected_fund = st.selectbox("Select a fund to view details:", fund_names)
    
    # Save the selected fund in session state
    st.session_state.selected_fund = selected_fund  # Save the selected fund in session_state

    # Now use this selected fund for further details
    st.write(f"Details for: {selected_fund}")

    # === Step 3: Scorecard Metrics ===
    st.markdown("**Scorecard Metrics**")
    blocks = st.session_state.get("fund_blocks", [])
    block = next((b for b in blocks if b["Fund Name"] == selected_fund), None)
    if block:
        for m in block["Metrics"]:
            st.write(f"- {m['Metric']}: {m['Info']}")
    else:
        st.write("_No scorecard data found._")

    # === Slide 1 Table ===
    st.markdown("**Slide 1 Table**")

    # 1) Category from factsheet
    fs_rec = next((f for f in facts if f["Matched Fund Name"] == selected_fund), {})
    category = fs_rec.get("Category","")

    # 2) Build first 11 IPS criteria
    IPS = [
      "Manager Tenure","Excess Performance (3Yr)","R‑Squared (3Yr)",
      "Peer Return Rank (3Yr)","Sharpe Ratio Rank (3Yr)","Sortino Ratio Rank (3Yr)",
      "Tracking Error Rank (3Yr)","Excess Performance (5Yr)","R‑Squared (5Yr)",
      "Peer Return Rank (5Yr)","Sharpe Ratio Rank (5Yr)"
    ]

    # 3) Compute pass/fail statuses for this fund
    statuses = {}
    # Manager Tenure ≥3
    info = next((m["Info"] for m in block["Metrics"] if m["Metric"]=="Manager Tenure"),"")
    yrs  = float(re.search(r"(\d+\.?\d*)",info).group(1)) if re.search(r"(\d+\.?\d*)",info) else 0
    statuses["Manager Tenure"] = (yrs >= 3)
    # Other criteria
    for crit in IPS[1:]:
        raw = next((m["Info"] for m in block["Metrics"] if m["Metric"].startswith(crit.split()[0])),"")
        if "Excess Performance" in crit:
            pct = float(re.search(r"([-+]?\d*\.\d+)%",raw).group(1)) if re.search(r"([-+]?\d*\.\d+)%",raw) else 0
            statuses[crit] = (pct > 0)
        elif "R‑Squared" in crit:
            statuses[crit] = True
        else:
            rk = int(re.search(r"(\d+)",raw).group(1)) if re.search(r"(\d+)",raw) else 999
            statuses[crit] = (rk <= 50)

    # 4) Determine overall IPS Status
    fails = sum(not statuses[c] for c in IPS)
    if   fails <= 4:  overall = "Passed IPS Screen"
    elif fails == 5:  overall = "Informal Watch (IW)"
    else:             overall = "Formal Watch (FW)"

    # … after you compute `overall = "Passed IPS Screen" …` etc.
    # Save it so our bullets can look it up:
    if "ips_status_map" not in st.session_state:
        st.session_state["ips_status_map"] = {}
    st.session_state["ips_status_map"][selected_fund] = overall


    # 5) Build the DataFrame row
    report_date = st.session_state.get("report_date","")
    row = {
      "Category":    category,
      "Time Period": report_date,
      "Plan Assets": "$"
    }
    for idx, crit in enumerate(IPS, start=1):
        row[str(idx)] = statuses[crit]
    row["IPS Status"] = overall

    df_slide1 = pd.DataFrame([row])

    # 6) Style it
    def color_bool(v): return "background-color: green" if v else "background-color: red"
    def style_status(v):
        if v=="Passed IPS Screen":    return "background-color: green; color: white"
        if "Informal Watch" in v:      return "background-color: orange; color: white"
        if "Formal Watch"   in v:      return "background-color: red;   color: white"
        return ""
    styled = df_slide1.style \
        .applymap(color_bool,   subset=[str(i) for i in range(1,len(IPS)+1)]) \
        .applymap(style_status, subset=["IPS Status"])

    st.dataframe(styled, use_container_width=True)

    # === Slide 2 Table 1 ===
    st.markdown("**Slide 2 Table 1**")
    # grab performance data for the selected fund
    perf_data = st.session_state.get("fund_performance_data", [])
    perf_item = next((p for p in perf_data if p.get("Fund Scorecard Name") == selected_fund), {})
    # build Investment Manager label with ticker
    inv_mgr = f"{selected_fund} ({perf_item.get('Ticker','')})"
    # extract Net Expense Ratio and append '%' if not already present
    net_exp = perf_item.get("Net Expense Ratio", "")
    if net_exp and not str(net_exp).endswith("%"):
        net_exp = f"{net_exp}%"
    # assemble and display
    df_slide2 = pd.DataFrame([{
        "Investment Manager": inv_mgr,
        "Net Expense Ratio":  net_exp
    }])
    st.dataframe(df_slide2, use_container_width=True)

    # === Slide 2 Table 2 ===
    st.markdown("**Slide 2 Table 2**")
    # grab the annualized returns for the selected fund
    perf_data = st.session_state.get("fund_performance_data", [])
    perf_item = next((p for p in perf_data if p.get("Fund Scorecard Name")==selected_fund), {})
    # build Investment Manager label with ticker in parentheses
    inv_mgr    = f"{selected_fund} ({perf_item.get('Ticker','')})"
    # use report_date as the QTD column header
    date_label = st.session_state.get("report_date", "QTD")

    # helper to append '%' if missing
    def append_pct(val):
        s = str(val) if val is not None else ""
        return s if s.endswith("%") or s=="" else f"{s}%"

    # extract and format each return
    qtd   = append_pct(perf_item.get("QTD",""))
    one   = append_pct(perf_item.get("1Yr",""))
    three = append_pct(perf_item.get("3Yr",""))
    five  = append_pct(perf_item.get("5Yr",""))
    ten   = append_pct(perf_item.get("10Yr",""))

    # assemble the row
    row = {
        "Investment Manager": inv_mgr,
        date_label:           qtd,
        "1 Year":             one,
        "3 Year":             three,
        "5 Year":             five,
        "10 Year":            ten
    }
    df_slide2_2 = pd.DataFrame([row])
    st.dataframe(df_slide2_2, use_container_width=True)

    # === Slide 2 Table 3 ===
    st.markdown("**Slide 2 Table 3**")
    
    # 1) Grab the calendar year returns extracted in Step 8 (fund and benchmark data)
    fund_cy = st.session_state.get("step8_returns", [])
    bench_cy = st.session_state.get("benchmark_calendar_year_returns", [])
    
    # Check if data exists
    if not fund_cy or not bench_cy:
        st.error("❌ No calendar year returns data found. Ensure Step 8 has been run correctly.")
        return
    
    # 2) Ensure 'Name' exists in the fund and benchmark records (using 'Name' instead of 'Fund Name')
    # Debugging output to check structure
    # st.write(f"Fund data keys: {fund_cy[0].keys() if fund_cy else 'No data'}")
   #  st.write(f"Benchmark data keys: {bench_cy[0].keys() if bench_cy else 'No data'}")
    
    # 3) Find the selected fund’s record and its benchmark record
    fund_rec = next((r for r in fund_cy if r.get("Name") == selected_fund), None)  # Changed "Fund Name" to "Name"
    if not fund_rec:
        st.error(f"❌ Could not find data for selected fund: {selected_fund}")
        return
    
    # 4) Try to match the benchmark data using Name or Ticker
    benchmark_name = selected_fund  # Assume benchmark matches the fund's name, we can refine this logic if needed
    bench_rec = next((r for r in bench_cy if r.get("Name") == benchmark_name or r.get("Ticker") == fund_rec.get("Ticker")), None)
    
    # If benchmark record is not found
    if not bench_rec:
        st.error(f"❌ Could not find benchmark data for selected fund: {selected_fund}")
        return
    
    # 5) Get the years from the calendar year columns (using the first record)
    year_cols = [col for col in fund_rec.keys() if re.match(r"20\d{2}", col)]
    
    # 6) Prepare the rows for the selected fund and benchmark
    rows = []
    
    # 7) Add the selected fund's data
    row_fund = {"Investment Manager": f"{selected_fund} ({fund_rec.get('Ticker','')})"}
    for year in year_cols:
        row_fund[year] = fund_rec.get(year, "")
    rows.append(row_fund)
    
    # 8) Add the benchmark's data, using the benchmark's name (or fallback)
    row_benchmark = {"Investment Manager": f"{bench_rec.get('Name', 'Benchmark')} ({bench_rec.get('Ticker', '')})"}
    for year in year_cols:
        row_benchmark[year] = bench_rec.get(year, "")
    rows.append(row_benchmark)
    
    # 9) Create a DataFrame for the table
    df_slide2_3 = pd.DataFrame(rows, columns=["Investment Manager"] + year_cols)
    
    # 10) Display the table
    st.dataframe(df_slide2_3, use_container_width=True)


    # === Slide 3 Table 1 ===
    st.markdown("**Slide 3 Table 1**")
    # grab 3‑Yr MPT stats
    mpt3 = st.session_state.get("step9_mpt_stats", [])
    stats3 = next((r for r in mpt3 if r["Fund Name"] == selected_fund), {})
    # grab 5‑Yr MPT stats
    mpt5 = st.session_state.get("step10_mpt_stats", [])
    stats5 = next((r for r in mpt5 if r["Fund Name"] == selected_fund), {})
    # build Investment Manager with ticker
    ticker = stats3.get("Ticker", stats5.get("Ticker", ""))
    inv_mgr = f"{selected_fund} ({ticker})"
    # assemble the row
    row = {
        "Investment Manager":        inv_mgr,
        "3 Year Alpha":              stats3.get("3 Year Alpha", ""),
        "5 Year Alpha":              stats5.get("5 Year Alpha", ""),
        "3 Year Beta":               stats3.get("3 Year Beta", ""),
        "5 Year Beta":               stats5.get("5 Year Beta", ""),
        "3 Year Upside Capture":     stats3.get("3 Year Upside Capture", ""),
        "3 Year Downside Capture":   stats3.get("3 Year Downside Capture", ""),
        "5 Year Upside Capture":     stats5.get("5 Year Upside Capture", ""),
        "5 Year Downside Capture":   stats5.get("5 Year Downside Capture", "")
    }
    df_slide3_1 = pd.DataFrame([row])
    st.dataframe(df_slide3_1, use_container_width=True)

    # === Slide 3 Table 2 ===
    st.markdown("**Slide 3 Table 2**")
    # grab risk‑adjusted returns and peer ranks for the selected fund
    risk_table = st.session_state.get("step13_risk_adjusted_table", [])
    peer_table = st.session_state.get("step14_peer_rank_table", [])
    risk_rec = next((r for r in risk_table if r["Fund Name"] == selected_fund), {})
    peer_rec = next((r for r in peer_table if r["Fund Name"] == selected_fund), {})
    
    # build Investment Manager label with ticker
    ticker = risk_rec.get("Ticker") or peer_rec.get("Ticker", "")
    inv_mgr = f"{selected_fund} ({ticker})"
    
    # helper to combine value and peer rank without calculation
    def frac(metric, period):
        r = risk_rec.get(f"{metric} {period}", "")
        p = peer_rec.get(f"{metric} {period}", "")
        return f"{r} / {p}"
    
    # assemble the row
    row = {
        "Investment Manager": inv_mgr,
        "3 Year Sharpe Ratio / Peer Ranking %": frac("Sharpe Ratio", "3Yr"),
        "5 Year Sharpe Ratio / Peer Ranking %": frac("Sharpe Ratio", "5Yr"),
        "3 Year Sortino Ratio / Peer Ranking %": frac("Sortino Ratio", "3Yr"),
        "5 Year Sortino Ratio / Peer Ranking %": frac("Sortino Ratio", "5Yr"),
        "3 Year Information Ratio / Peer Ranking %": frac("Information Ratio", "3Yr"),
        "5 Year Information Ratio / Peer Ranking %": frac("Information Ratio", "5Yr"),
    }
    
    df_slide3_2 = pd.DataFrame([row])
    st.dataframe(df_slide3_2, use_container_width=True)

    
    # === Slide 4 Table 1 ===
    st.markdown("**Slide 4 Table 1**")
    # grab the scorecard metrics for the selected fund
    blocks      = st.session_state.get("fund_blocks", [])
    block       = next((b for b in blocks if b["Fund Name"] == selected_fund), {})
    raw_tenure  = next((m["Info"] for m in block.get("Metrics", []) if m["Metric"] == "Manager Tenure"), "")
    # extract just the numeric years and append "years"
    import re
    m = re.search(r"(\d+(\.\d+)?)", raw_tenure)
    tenure = f"{m.group(1)} years" if m else raw_tenure

    # build Investment Manager label with ticker
    perf_data = st.session_state.get("fund_performance_data", [])
    perf_item = next((p for p in perf_data if p.get("Fund Scorecard Name") == selected_fund), {})
    inv_mgr   = f"{selected_fund} ({perf_item.get('Ticker','')})"

    # assemble and display
    df_slide4 = pd.DataFrame([{
        "Investment Manager": inv_mgr,
        "Manager Tenure":     tenure
    }])
    st.dataframe(df_slide4, use_container_width=True)

    # === Slide 4 Table 2 ===
    st.markdown("**Slide 4 Table 2**")
    # grab factsheet details for the selected fund
    facts = st.session_state.get("fund_factsheets_data", [])
    fs_rec = next((f for f in facts if f["Matched Fund Name"] == selected_fund), {})
    # grab ticker for label
    perf_data = st.session_state.get("fund_performance_data", [])
    perf_item = next((p for p in perf_data if p["Fund Scorecard Name"] == selected_fund), {})
    # build Investment Manager label
    inv_mgr    = f"{selected_fund} ({perf_item.get('Ticker','')})"
    # extract Net Assets and Avg. Market Cap
    assets     = fs_rec.get("Net Assets", "")
    avg_cap    = fs_rec.get("Avg. Market Cap", "")
    # assemble and display
    df_slide4_2 = pd.DataFrame([{
        "Investment Manager":             inv_mgr,
        "Assets Under Management":        assets,
        "Average Market Capitalization":  avg_cap
    }])
    st.dataframe(df_slide4_2, use_container_width=True)


def step16_bullet_points():
    import streamlit as st

    st.subheader("Step 16: Bullet Points")

    selected_fund = st.session_state.get("selected_fund")
    if not selected_fund:
        st.error("❌ No fund selected. Please select a fund in Step 15.")
        return

    perf_data = st.session_state.get("fund_performance_data", [])
    item = next((x for x in perf_data if x["Fund Scorecard Name"] == selected_fund), None)
    if not item:
        st.error(f"❌ Performance data for '{selected_fund}' not found.")
        return

    # — Bullet 1: Performance vs. Benchmark —
    template = st.session_state.get("bullet_point_templates", [""])[0]
    b1 = template
    for fld, val in item.items():
        b1 = b1.replace(f"[{fld}]", str(val))
    st.markdown(f"- {b1}")

    # — Bullet 2: IPS Screening Status & Returns Comparison —
    ips_status = st.session_state.get("ips_status_map", {}).get(selected_fund, "")

    if "Passed" in ips_status:
        st.markdown("- This fund is not on watch.")
    else:
        if "Formal" in ips_status:
            status_label = "Formal Watch"
        elif "Informal" in ips_status:
            status_label = "Informal Watch"
        else:
            status_label = ips_status or "on watch"

        three   = float(item.get("3Yr")      or 0)
        bench3  = float(item.get("Bench 3Yr") or 0)
        five    = float(item.get("5Yr")      or 0)
        bench5  = float(item.get("Bench 5Yr") or 0)
        bps3 = round((three  - bench3)*100, 1)
        bps5 = round((five   - bench5)*100, 1)

        peer = st.session_state.get("step14_peer_rank_table", [])
        raw3 = next((r.get("Sharpe Ratio Rank 3Yr") for r in peer
                     if r.get("Fund Name") == selected_fund), None)
        raw5 = next((r.get("Sharpe Ratio Rank 5Yr") for r in peer
                     if r.get("Fund Name") == selected_fund), None)
        try:
            pos3 = "top" if int(raw3) <= 50 else "bottom"
        except:
            pos3 = "bottom"
        try:
            pos5 = "top" if int(raw5) <= 50 else "bottom"
        except:
            pos5 = "bottom"

        st.markdown(
            f"- The fund is now on {status_label}. Its three‑year return trails the benchmark by "
            f"{bps3} bps ({three:.2f}% vs. {bench3:.2f}%) and its five‑year return trails by "
            f"{bps5} bps ({five:.2f}% vs. {bench5:.2f}%). Its 3‑Yr Sharpe ranks in the {pos3} half of peers "
            f"and its 5‑Yr Sharpe ranks in the {pos5} half."
        )

    # — Bullet 3: Action for Formal Watch only —
    if "Formal" in ips_status:
        st.markdown("- **Action:** Consider replacing this fund.")


#─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# === Main App ===
# Main App
def run():
    import re
    st.title("Writeup")
    
    # Upload MPI PDF
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    # Open the PDF
    with pdfplumber.open(uploaded) as pdf:
        # Step 1: Process Page 1
        with st.expander("Step 1: Details", expanded=False):
            first = pdf.pages[0].extract_text() or ""
            process_page1(first)

        # Step 2: Process Table of Contents
        with st.expander("Step 2: Table of Contents", expanded=False):
            toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
            process_toc(toc_text)

        # Step 3: Process Scorecard Metrics
        with st.expander("Step 3: Scorecard Metrics", expanded=False):
            sp = st.session_state.get('scorecard_page')
            tot = st.session_state.get('total_options')
            if sp and tot is not None:
                step3_process_scorecard(pdf, sp, tot)
            else:
                st.error("Missing scorecard page or total options")

        # Step 4: Process IPS Screening
        with st.expander("Step 4: IPS Screening", expanded=False):
            step4_ips_screen()

        # Step 5: Process Fund Performance
        with st.expander("Step 5: Fund Performance", expanded=False):
            pp = st.session_state.get('performance_page')
            names = [b['Fund Name'] for b in st.session_state.get('fund_blocks', [])]
            if pp and names:
                step5_process_performance(pdf, pp, names)
            else:
                st.error("Missing performance page or fund blocks")

        # Step 6: Process Fund Factsheets
        with st.expander("Step 6: Fund Factsheets", expanded=True):
            names = [b['Fund Name'] for b in st.session_state.get('fund_blocks', [])]
            step6_process_factsheets(pdf, names)

        # Step 7: Extract Returns
        with st.expander("Step 7: Annualized Returns", expanded=False):
            step7_extract_returns(pdf)

        # Data Prep for Bullet Points
        prepare_bullet_points_data()

        # Step 8: Calendar Year Returns
        with st.expander("Step 8: Calendar Year Returns", expanded=False):
            step8_calendar_returns(pdf)

        # Step 9: Risk Analysis 3-Year
        with st.expander("Step 9: Risk Analysis (3Yr)", expanded=False):
            step9_risk_analysis_3yr(pdf)

        # Step 10: Risk Analysis 5-Year
        with st.expander("Step 10: Risk Analysis (5Yr)", expanded=False):
            step10_risk_analysis_5yr(pdf)

        # Step 11: MPT Statistics Summary
        with st.expander("Step 11: MPT Statistics Summary", expanded=False):
            step11_create_summary()

        # Step 12: Fund Facts
        with st.expander("Step 12: Fund Facts", expanded=False):
            step12_process_fund_facts(pdf)

        # Step 13: Risk-Adjusted Returns
        with st.expander("Step 13: Risk-Adjusted Returns", expanded=False):
            step13_process_risk_adjusted_returns(pdf)

        # Step 14: Peer Risk-Adjusted Return Rank
        with st.expander("Step 14: Peer Risk-Adjusted Return Rank", expanded=False):
            step14_extract_peer_risk_adjusted_return_rank(pdf)

        # Step 15: View Single Fund Details
        with st.expander("Step 15: Single Fund Details", expanded=False):
            step15_display_selected_fund()

        # Step 16: Bullet Points
        with st.expander("Step 16: Bullet Points", expanded=False):
            step16_bullet_points()


def prepare_bullet_points_data():
    report_date = st.session_state.get("report_date", "")
    m = re.match(r"(\d)(?:st|nd|rd|th)\s+QTR,\s*(\d{4})", report_date)
    quarter = m.group(1) if m else ""
    year    = m.group(2) if m else ""
    
    # Ensure the data is iterated through
    for itm in st.session_state.get("fund_performance_data", []):
        # Force numeric defaults
        qtd       = float(itm.get("QTD") or 0)
        bench_qtd = float(itm.get("Bench QTD") or 0)
        
        # Direction, Quarter and Year
        itm["Perf Direction"] = "overperformed" if qtd >= bench_qtd else "underperformed"
        itm["Quarter"]        = quarter
        itm["Year"]           = year
        
        # Basis-points difference
        diff_bps = round((qtd - bench_qtd) * 100, 1)
        itm["QTD_bps_diff"] = str(diff_bps)
        
        # Percent strings
        fund_pct  = f"{qtd:.2f}%"
        bench_pct = f"{bench_qtd:.2f}%"
        itm["QTD_pct_diff"] = f"{(qtd - bench_qtd):.2f}%"
        itm["QTD_vs"]       = f"{fund_pct} vs. {bench_pct}"
    
    # Initialize template
    if "bullet_point_templates" not in st.session_state:
        st.session_state["bullet_point_templates"] = [
            "[Fund Scorecard Name] [Perf Direction] its benchmark in Q[Quarter], "
            "[Year] by [QTD_bps_diff] bps ([QTD_vs])."
        ]

            


if __name__ == "__main__":
    run()
