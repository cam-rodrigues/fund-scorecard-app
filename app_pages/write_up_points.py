import re
import streamlit as st
import pdfplumber
from calendar import month_name
import pandas as pd
from rapidfuzz import fuzz

# === Utility: Extract & Label Report Date ===
def extract_report_date(text):
    # find the first quarter‐end or any mm/dd/yyyy
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(20\d{2})', text or "")
    for month, day, year in dates:
        m, d = int(month), int(day)
        # quarter‐end mapping
        if (m, d) in [(3,31), (6,30), (9,30), (12,31)]:
            q = { (3,31): "1st", (6,30): "2nd", (9,30): "3rd", (12,31): "4th" }[(m,d)]
            return f"{q} QTR, {year}"
        # fallback: human‐readable
        return f"As of {month_name[m]} {d}, {year}"
    return None
    
# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    report_date = extract_report_date(text)
    if report_date:
        st.session_state['report_date'] = report_date
        st.success(f"Report Date: {report_date}")
    else:
        st.error("Could not detect report date on page 1.")

    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state['total_options'] = int(m.group(1)) if m else None

    m = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state['prepared_for'] = m.group(1).strip() if m else None

    m = re.search(r"Prepared By:\s*(.*)", text or "")
    pb = m.group(1).strip() if m else ""
    if not pb or "mpi stylus" in pb.lower():
        pb = "Procyon Partners, LLC"
    st.session_state['prepared_by'] = pb

    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: {pb}")


# === Step 2: Table of Contents Extraction ===
def process_toc(text):
    perf = re.search(r"Fund Performance[^\d]*(\d{1,3})", text or "")
    sc   = re.search(r"Fund Scorecard\s+(\d{1,3})", text or "")
    fs   = re.search(r"Fund Factsheets\s+(\d{1,3})", text or "")
    cy   = re.search(r"Fund Performance: Calendar Year\s+(\d{1,3})", text or "")
    r3yr = re.search(r"Risk Analysis: MPT Statistics \(3Yr\)\s+(\d{1,3})", text or "")
    r5yr = re.search(r"Risk Analysis: MPT Statistics \(5Yr\)\s+(\d{1,3})", text or "")

    perf_page = int(perf.group(1)) if perf else None
    sc_page   = int(sc.group(1))   if sc   else None
    fs_page   = int(fs.group(1))   if fs   else None
    cy_page   = int(cy.group(1))   if cy   else None
    r3yr_page = int(r3yr.group(1)) if r3yr else None
    r5yr_page = int(r5yr.group(1)) if r5yr else None

    st.subheader("Table of Contents Pages")
    st.write(f"- Fund Performance Current vs Proposed Comparison : {perf_page}")
    st.write(f"- Fund Performance Calendar Year : {cy_page}")
    st.write(f"- MPT 3Yr Risk Analysis : {r3yr_page}")
    st.write(f"- MPT 5Yr Risk Analysis : {r5yr_page}")
    st.write(f"- Fund Scorecard:   {sc_page}")
    st.write(f"- Fund Factsheets :  {fs_page}")
    


    # Store in session state for future reference
    st.session_state['performance_page'] = perf_page
    st.session_state['scorecard_page']   = sc_page
    st.session_state['factsheets_page']  = fs_page
    st.session_state['calendar_year_page'] = cy_page
    st.session_state['r3yr_page'] = r3yr_page
    st.session_state['r5yr_page'] = r5yr_page



# === Step 3 ===
def step3_process_scorecard(pdf, start_page, declared_total):
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()

    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    fund_blocks = []
    name = None
    metrics = []

    for i,line in enumerate(lines):
        m = re.match(r"^(.*?)\s+(Pass|Review)\s+(.+)$", line.strip())
        if not m:
            continue
        metric, _, info = m.groups()

        if metric == "Manager Tenure":
            if name and metrics:
                fund_blocks.append({"Fund Name": name, "Metrics": metrics})
            # find the fund name from the previous non-blank line
            prev = ""
            for j in range(i-1, -1, -1):
                if lines[j].strip():
                    prev = lines[j].strip()
                    break
            name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            metrics = []

        if name:
            metrics.append({"Metric": metric, "Info": info})

    if name and metrics:
        fund_blocks.append({"Fund Name": name, "Metrics": metrics})

    st.session_state["fund_blocks"] = fund_blocks

    st.subheader("Step 3.5: Key Details per Metric")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            st.write(f"- **{m['Metric']}**: {m['Info'].strip()}")

    st.subheader("Step 3.6: Investment Option Count")
    count = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{count}**")
    if count == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Expected {declared_total}, found {count}.")

# === Step 4: IPS Screening ===
def step4_ips_screen():
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
        is_passive = "bitcoin" in name.lower()
        statuses, reasons = {}, {}

        # Manager Tenure ≥3
        info = next((m["Info"] for m in b["Metrics"] if m["Metric"]=="Manager Tenure"), "")
        yrs = float(re.search(r"(\d+\.?\d*)", info).group(1)) if re.search(r"(\d+\.?\d*)", info) else 0
        ok = yrs>=3
        statuses["Manager Tenure"] = ok
        reasons["Manager Tenure"] = f"{yrs} yrs {'≥3' if ok else '<3'}"

        # map each IPS metric
        for metric in IPS[1:]:  # skip tenure
            m = next((x for x in b["Metrics"] if x["Metric"].startswith(metric.split()[0])), None)
            info = m["Info"] if m else ""
            if "Excess Performance" in metric:
                val_m = re.search(r"([-+]?\d*\.\d+)%", info)
                val = float(val_m.group(1)) if val_m else 0
                ok = (val>0) if "3Yr" in metric else (val>0)
                statuses[metric] = ok
                reasons[metric] = f"{val}%"
            elif "R-Squared" in metric:
                pct_m = re.search(r"(\d+\.\d+)%", info)
                pct = float(pct_m.group(1)) if pct_m else 0
                ok = (pct>=95) if is_passive else True
                statuses[metric] = ok
                reasons[metric] = f"{pct}%"
            elif "Peer Return" in metric or "Sharpe Ratio" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                ok = rank<=50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"
            elif "Sortino Ratio" in metric or "Tracking Error" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                if "Sortino" in metric and not is_passive:
                    ok = rank<=50
                elif "Tracking Error" in metric and is_passive:
                    ok = rank<90
                else:
                    ok = True
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"
            elif "Expense Ratio" in metric:
                rank_m = re.search(r"(\d+)", info)
                rank = int(rank_m.group(1)) if rank_m else 999
                ok = rank<=50
                statuses[metric] = ok
                reasons[metric] = f"Rank {rank}"

        # count fails
        fails = sum(not v for v in statuses.values())
        if fails<=4:
            overall="Passed IPS Screen"
        elif fails==5:
            overall="Informal Watch (IW)"
        else:
            overall="Formal Watch (FW)"

        st.markdown(f"### {name} ({'Passive' if is_passive else 'Active'})")
        st.write(f"**Overall:** {overall} ({fails} fails)")
        for m in IPS:
            sym = "✅" if statuses.get(m,False) else "❌"
            st.write(f"- {sym} **{m}**: {reasons.get(m,'—')}")


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


# === Step 7: QTD, 1Yr, 3Yr, 5Yr, 10Yr Annualized Returns ===
def step7_extract_returns(pdf):
    st.subheader("Step 7: QTD / 1Yr / 3Yr / 5Yr / 10Yr Returns")

    perf_page = st.session_state.get("performance_page")
    perf_data = st.session_state.get("fund_performance_data", [])

    if perf_page is None or not perf_data:
        st.error("❌ Run Step 5 first to populate performance data.")
        return

    return_fields = [
        "QTD", "1Yr", "3Yr", "5Yr", "10Yr",
        "Benchmark QTD", "Benchmark 1Yr", "Benchmark 3Yr", "Benchmark 5Yr", "Benchmark 10Yr"
    ]
    for item in perf_data:
        for field in return_fields:
            item.setdefault(field, None)

    # Define is_filled() to check if all returns are populated
    def is_filled(item):
        return all(item.get(f) not in [None, ""] for f in return_fields)

    # === Read the Fund Performance pages only ===
    lines = []
    start = (perf_page or 1) - 1
    for i in range(start, len(pdf.pages)):
        page = pdf.pages[i]
        text = page.extract_text() or ""
        if "Fund Performance: Current vs." not in text:
            break  # Stop when section ends

        page_lines = [l.strip() for l in text.splitlines() if l.strip()]
        lines.extend(page_lines)

    matched_count = 0
    i = 0
    while i < len(lines) - 3:
        row = lines[i]
        next1 = lines[i + 1]
        next2 = lines[i + 2] if i + 2 < len(lines) else ""
        next3 = lines[i + 3] if i + 3 < len(lines) else ""

        # Match return rows with 8 numeric values (QTD, 1Yr, 3Yr, 5Yr, 10Yr)
        num_re = re.compile(r'^-?\d+\.\d+(\s+-?\d+\.\d+){7}$')
        if not num_re.match(row):
            i += 1
            continue

        parts = re.split(r'\s+', row)
        QTD_, ONE_YR, THREE_YR, FIVE_YR, TEN_YR = parts[0], parts[2], parts[3], parts[4], parts[5]

        # Fund line should be next
        fund_line = next1
        ticker_match = re.search(r'\b[A-Z]{4,6}\b', fund_line)
        ticker = ticker_match.group(0).strip() if ticker_match else None

        # Benchmark line (may not exist)
        bench_line = next3
        bparts = re.split(r'\s+', bench_line)
        bvals = bparts[-6:] if len(bparts) >= 6 else [None]*6
        bQTD, b1YR, b3YR, b5YR, b10YR = bvals[0:5]

        # Loop through all funds to match
        for item in perf_data:
            if is_filled(item):
                continue

            name = item.get("Fund Scorecard Name", "")
            tk = item.get("Ticker", "")
            score = fuzz.token_sort_ratio(f"{name} {tk}".lower(), fund_line.lower())
            ticker_ok = tk.upper() == (ticker or "").upper()

            # Dynamically detect and fill returns for retirement funds or missing benchmarks
            if score > 70 or ticker_ok:
                if not item["QTD"]:             item["QTD"] = QTD_
                if not item["1Yr"]:             item["1Yr"] = ONE_YR
                if not item["3Yr"]:             item["3Yr"] = THREE_YR
                if not item["5Yr"]:             item["5Yr"] = FIVE_YR
                if not item["10Yr"]:            item["10Yr"] = TEN_YR
                if bQTD and not item["Benchmark QTD"]:   item["Benchmark QTD"] = bQTD
                if b1YR and not item["Benchmark 1Yr"]:   item["Benchmark 1Yr"] = b1YR
                if b3YR and not item["Benchmark 3Yr"]:   item["Benchmark 3Yr"] = b3YR
                if b5YR and not item["Benchmark 5Yr"]:   item["Benchmark 5Yr"] = b5YR
                if b10YR and not item["Benchmark 10Yr"]: item["Benchmark 10Yr"] = b10YR
                matched_count += 1
                break

        i += 1

    # Update session data
    st.session_state["fund_performance_data"] = perf_data
    df = pd.DataFrame(perf_data)

    # Prepare columns to display
    display_cols = ["Fund Scorecard Name", "Ticker"] + return_fields
    missing = [c for c in display_cols if c not in df.columns]
    if missing:
        st.error(f"Expected columns {display_cols}, but missing {missing}.")
        return

    # Output the results
    st.success(f"✅ Matched {matched_count} fund(s) with return data.")

    # Debug: Log missing funds
    for item in perf_data:
        if not is_filled(item):
            st.warning(f"⚠️ Could not fully fill: {item['Fund Scorecard Name']} ({item['Ticker']})")

    st.dataframe(df[display_cols], use_container_width=True)

# === Step 8a: Match Saved Tickers & Fund Names in the Calendar Year Section ===
# Mirrors Step 5’s approach but targets the Calendar Year Performance section.
# === Step 8: Match Tickers in “Calendar Year Performance” Section ===
def step8_match_calendar_tickers(pdf):
    import re, streamlit as st

    st.subheader("Step 8: Match Tickers in Calendar Year Section")

    # 1) Your original fund→ticker mapping from Step 5
    fund_map5 = st.session_state.get("tickers", {})
    if not fund_map5:
        st.error("❌ No ticker mapping found. Run Step 5 first.")
        return

    # 2) Find the start page of "Calendar Year Performance"
    section_page = None
    for idx, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        if "Calendar Year Performance" in text:
            section_page = idx
            break

    if section_page is None:
        st.error("❌ Could not find the Calendar Year Performance section.")
        return

    # 3) Scan from that page onward, until all funds are found
    found    = {}
    locs     = {}
    total    = len(fund_map5)

    for pnum in range(section_page, len(pdf.pages) + 1):
        lines = (pdf.pages[pnum-1].extract_text() or "").splitlines()
        for li, ln in enumerate(lines):
            tokens = ln.split()
            for fname, tk in fund_map5.items():
                if fname in found: 
                    continue
                ticker = tk.upper()
                if ticker in tokens:
                    found[fname] = ticker
                    locs[fname]  = {"page": pnum, "line": li}
        if len(found) == total:
            break

    # 4) Save and display
    st.session_state["step8_tickers"]   = found
    st.session_state["step8_locations"] = locs
    st.session_state["step8_start_page"] = section_page

    st.subheader("Extracted Tickers & Locations (Step 8)")
    for name in fund_map5:
        if name in found:
            info = locs[name]
            st.write(f"- {name}: {found[name]} (page {info['page']}, line {info['line']+1}) ✅")
        else:
            st.write(f"- {name}: ❌ not found")

    st.subheader("Ticker Count Validation")
    st.write(f"- Expected: **{total}**")
    st.write(f"- Found:    **{len(found)}**")
    if len(found) == total:
        st.success("✅ All tickers found.")
    else:
        st.error(f"❌ Missing {total - len(found)} ticker(s).")

# === Step 8.5: Extract Calendar Year Returns ===
def step8_5_extract_calendar_returns(pdf):
    import re, pandas as pd, streamlit as st

    st.subheader("Step 8.5: Calendar Year Returns")

    tickers_map = st.session_state.get("step8_tickers", {})
    start_pg    = st.session_state.get("step8_start_page", 1)
    if not tickers_map:
        st.error("❌ No ticker mapping found. Run Step 8 first.")
        return

    # 1) Find header row to get year labels
    header_line = None
    for pnum in range(start_pg-1, len(pdf.pages)):
        for ln in (pdf.pages[pnum].extract_text() or "").splitlines():
            if "Ticker" in ln and "2015" in ln:
                header_line = ln
                break
        if header_line:
            break
    if not header_line:
        st.error("❌ Couldn’t find header row with Ticker+2015.")
        return

    years = re.findall(r"\b20(1[5-9]|2[0-4])\b", header_line)
    years = ["20" + y for y in years]
    n = len(years)

    # regex to grab numeric values (allowing parentheses and %)
    num_rx = re.compile(r"\(?-?\d+\.\d+%?\)?")

    results = []
    for name, ticker in tickers_map.items():
        ticker = ticker.upper()
        vals = None

        # scan from section start forward
        for pnum in range(start_pg-1, len(pdf.pages)):
            lines = (pdf.pages[pnum].extract_text() or "").splitlines()
            idx = next((i for i, ln in enumerate(lines) if ticker in ln), None)
            if idx is not None:
                num_line = lines[idx-1] if idx > 0 else ""
                raw = num_rx.findall(num_line)
                clean = [t.strip("()%").rstrip("%") for t in raw]
                if len(clean) < n:
                    clean += [None] * (n - len(clean))
                vals = clean[:n]
                break

        if not vals:
            vals = [None] * n

        results.append({
            "Fund Name": name,
            "Ticker":    ticker,
            **{years[i]: vals[i] for i in range(n)}
        })

    df = pd.DataFrame(results)
    st.session_state["step8_returns"] = results
    st.dataframe(df)


#-------------------------------------------------------------------------------------------

# === Main App ===
def run():
    st.title("Writeup")
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        return

    with pdfplumber.open(uploaded) as pdf:
        # Step 1
        with st.expander("Step 1: Page 1 Extraction", expanded=False):
            first = pdf.pages[0].extract_text() or ""
            process_page1(first)

        # Step 2
        with st.expander("Step 2: Table of Contents Extraction", expanded=False):
            toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
            process_toc(toc_text)

        # Step 3
        with st.expander("Step 3: Scorecard Extraction", expanded=False):
            sp = st.session_state.get('scorecard_page')
            tot = st.session_state.get('total_options')
            if sp and tot is not None:
                step3_process_scorecard(pdf, sp, tot)
            else:
                st.error("Missing scorecard page or total options")

        # Step 4
        with st.expander("Step 4: IPS Screening", expanded=False):
            step4_ips_screen()

        # Step 5
        with st.expander("Step 5: Fund Performance Extraction", expanded=False):
            pp = st.session_state.get('performance_page')
            names = [b['Fund Name'] for b in st.session_state.get('fund_blocks', [])]
            if pp and names:
                step5_process_performance(pdf, pp, names)
            else:
                st.error("Missing performance page or fund blocks")

        # Step 6
        with st.expander("Step 6: Fund Factsheets Extraction", expanded=True):
            names = [b['Fund Name'] for b in st.session_state.get('fund_blocks', [])]
            step6_process_factsheets(pdf, names)

        # Step 7
        with st.expander("Step 7: Extract Annualized Returns", expanded=False):
            step7_extract_returns(pdf)
        
        # Step 8: Match Tickers
        with st.expander("Step 8: Match Tickers in Calendar Year Section", expanded=False):
            step8_match_calendar_tickers(pdf)
        
        # Step 8.5: Extract Calendar Year Returns
        with st.expander("Step 8.5: Extract Calendar Year Returns", expanded=False):
            step8_5_extract_calendar_returns(pdf)



if __name__ == "__main__":
    run()

