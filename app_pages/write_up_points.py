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

# === Step 7: QTD / 1Yr / 3Yr / 5Yr / 10Yr & Net Expense Ratio ===
def step7_extract_returns(pdf):
    import re
    import pandas as pd
    import streamlit as st
    from rapidfuzz import fuzz

    st.subheader("Step 7: QTD / 1Yr / 3Yr / 5Yr / 10Yr & Net Expense Ratio")

    # 1) Where to scan
    perf_page = st.session_state.get("performance_page")
    end_page  = st.session_state.get("calendar_year_page") or (len(pdf.pages) + 1)
    perf_data = st.session_state.get("fund_performance_data", [])
    if perf_page is None or not perf_data:
        st.error("❌ Run Step 5 first to populate performance data.")
        return

    # 2) Prep output slots
    fields = ["QTD", "1Yr", "3Yr", "5Yr", "10Yr", "Net Expense Ratio"]
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

        # a) Try exact ticker match
        idx = next(
            (i for i, ln in enumerate(lines)
             if re.search(rf"\b{re.escape(tk)}\b", ln)),
            None
        )

        # b) Fuzzy‑name fallback
        if idx is None:
            scores = [(i, fuzz.token_sort_ratio(name.lower(), ln.lower()))
                      for i, ln in enumerate(lines)]
            best_i, best_score = max(scores, key=lambda x: x[1])
            if best_score > 60:
                idx = best_i
            else:
                st.warning(f"⚠️ {name} ({tk}): no ticker or name match found.")
                continue

        # c) Need at least one line above to get numbers
        if idx == 0:
            st.warning(f"⚠️ {name} ({tk}): nothing above matched line to extract returns.")
            continue

        # d) Pull all decimals from the line above
        raw = num_rx.findall(lines[idx - 1])

        # e) If fewer than 8 tokens, also prepend from two lines above
        if len(raw) < 8 and idx >= 2:
            raw = num_rx.findall(lines[idx - 2]) + raw

        # f) Clean and pad to exactly 8 slots
        clean = [n.strip("()%").rstrip("%") for n in raw]
        if len(clean) < 8:
            clean += [None] * (8 - len(clean))

        # g) Map returns and net expense:
        #    idx 0=QTD, 2=1Yr, 3=3Yr, 4=5Yr, 5=10Yr, (-2)=Net Expense Ratio
        item["QTD"]               = clean[0]
        item["1Yr"]               = clean[2]
        item["3Yr"]               = clean[3]
        item["5Yr"]               = clean[4]
        item["10Yr"]              = clean[5]
        item["Net Expense Ratio"] = clean[-2]

        matched += 1

    # 5) Save back to session and display
    st.session_state["fund_performance_data"] = perf_data
    df = pd.DataFrame(perf_data)

    st.success(f"✅ Matched {matched} fund(s) with return data.")
    for itm in perf_data:
        if any(itm[f] in (None, "") for f in fields):
            st.warning(f"⚠️ Incomplete for {itm['Fund Scorecard Name']} ({itm['Ticker']})")

    st.dataframe(
        df[["Fund Scorecard Name", "Ticker"] + fields],
        use_container_width=True
    )


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

# === Step 9: Match Tickers in the Risk Analysis (3Yr) Section ===
def step9_match_risk_tickers(pdf):
    import re, streamlit as st

    st.subheader("Step 9: Match Tickers in Risk Analysis (3Yr)")

    # 1) your original fund→ticker map from Step 5
    fund_map = st.session_state.get("tickers", {})
    if not fund_map:
        st.error("❌ No ticker mapping found. Run Step 5 first.")
        return

    # 2) locate the start page of “Risk Analysis: MPT Statistics (3Yr)”
    section_page = st.session_state.get("r3yr_page")
    if not section_page:
        st.error("❌ ‘Risk Analysis: MPT Statistics (3Yr)’ page not found; run Step 2 first.")
        return

    # 3) scan from that page forward until all tickers are found
    found, locs = {}, {}
    total = len(fund_map)
    for pnum in range(section_page, len(pdf.pages) + 1):
        lines = (pdf.pages[pnum-1].extract_text() or "").splitlines()
        for li, ln in enumerate(lines):
            tokens = ln.split()
            for fname, tk in fund_map.items():
                if fname in found:
                    continue
                if tk.upper() in tokens:
                    found[fname] = tk.upper()
                    locs[fname]  = {"page": pnum, "line": li}
        if len(found) == total:
            break

    # 4) save & report
    st.session_state["step9_tickers"]   = found
    st.session_state["step9_locations"] = locs
    st.session_state["step9_start_page"] = section_page

    st.subheader("Extracted Tickers & Locations (Step 9)")
    for name in fund_map:
        if name in found:
            info = locs[name]
            st.write(f"- {name}: {found[name]} (page {info['page']}, line {info['line']+1}) ✅")
        else:
            st.write(f"- {name}: ❌ not found")

    st.subheader("Ticker Count Validation")
    st.write(f"- Expected: **{total}**")
    st.write(f"- Found:    **{len(found)}**")
    if len(found) == total:
        st.success("✅ All tickers found.")
    else:
        st.error(f"❌ Missing {total - len(found)} ticker(s).")


# === Step 9.5: Extract 3‑Yr MPT Statistics (renamed columns) ===
def step9_extract_mpt_statistics(pdf):
    import re, pandas as pd, streamlit as st

    st.subheader("Step 9.5: Extract MPT Statistics (3Yr)")

    # 1) Load the mapping & locations from Step 9
    tickers = st.session_state.get("step9_tickers", {})
    locs    = st.session_state.get("step9_locations", {})
    if not tickers or not locs:
        st.error("❌ Missing Step 9 data. Run Step 9 first.")
        return

    # 2) Regex to grab floats
    num_rx = re.compile(r"-?\d+\.\d+")

    results = []
    for name, ticker in tickers.items():
        info = locs.get(name)
        if not info:
            continue
        page = pdf.pages[info["page"] - 1]
        lines = (page.extract_text() or "").splitlines()
        line = lines[info["line"]] if info["line"] < len(lines) else ""

        # 3) Pull the first four numeric tokens from that line
        nums = num_rx.findall(line)
        nums += [None] * (4 - len(nums))
        alpha, beta, up_mkt, down_mkt = nums[:4]

        results.append({
            "Fund Name":                name,
            "Ticker":                   ticker.upper(),
            "3 Year Alpha":             alpha,
            "3 Year Beta":              beta,
            "3 Year Upside Capture":    up_mkt,
            "3 Year Downside Capture":  down_mkt
        })

    # 4) Render
    df = pd.DataFrame(results)
    st.session_state["step9_mpt_stats"] = results
    st.dataframe(df)


# === Step 10: Match Tickers in Risk Analysis (5Yr) Section ===
def step10_match_risk_tickers(pdf):
    import streamlit as st

    st.subheader("Step 10: Match Tickers in Risk Analysis (5Yr)")

    # 1) Your fund→ticker map from Step 5
    fund_map = st.session_state.get("tickers", {})
    if not fund_map:
        st.error("❌ No ticker mapping found. Run Step 5 first.")
        return

    # 2) Locate the 5‑Yr section
    section_page = next((
        i for i, pg in enumerate(pdf.pages, start=1)
        if "Risk Analysis: MPT Statistics (5Yr)" in (pg.extract_text() or "")
    ), None)
    if section_page is None:
        st.error("❌ Could not find ‘Risk Analysis: MPT Statistics (5Yr)’ section.")
        return

    # 3) Scan from that page until all tickers are found
    found, locs = {}, {}
    total = len(fund_map)
    for pnum in range(section_page, len(pdf.pages) + 1):
        lines = (pdf.pages[pnum-1].extract_text() or "").splitlines()
        for li, ln in enumerate(lines):
            tokens = ln.split()
            for name, tk in fund_map.items():
                if name in found:
                    continue
                if tk.upper() in tokens:
                    found[name] = tk.upper()
                    locs[name] = {"page": pnum, "line": li}
        if len(found) == total:
            break

    # 4) Save & display
    st.session_state["step10_tickers"]    = found
    st.session_state["step10_locations"]  = locs
    st.session_state["step10_start_page"] = section_page

    st.subheader("Extracted Tickers & Locations (Step 10)")
    for name in fund_map:
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


# === Step 10.5: Extract 5‑Yr MPT Statistics with Wrap‑Aware Parsing ===
def step10_extract_mpt_statistics(pdf):
    import re, pandas as pd, streamlit as st

    st.subheader("Step 10.5: Extract MPT Statistics (5Yr)")

    # 1) Load Step 10 mapping & locations
    tickers = st.session_state.get("step10_tickers", {})
    locs     = st.session_state.get("step10_locations", {})
    if not tickers or not locs:
        st.error("❌ Missing Step 10 data. Run Step 10 first.")
        return

    # 2) Regex for floats (no parentheses)
    num_rx = re.compile(r"-?\d+\.\d+")

    results = []
    for name, tk in tickers.items():
        info = locs[name]
        page = pdf.pages[info["page"] - 1]
        lines = (page.extract_text() or "").splitlines()

        # 3) Find the line index containing the ticker
        idx = next((i for i, ln in enumerate(lines) if tk in ln), None)
        if idx is None:
            st.warning(f"⚠️ {name} ({tk}): ticker line not found on page {info['page']}.")
            vals = [None]*4
        else:
            # 4) Accumulate numeric tokens from this line + next up to 2 lines
            nums = []
            for j in range(idx, min(idx + 3, len(lines))):
                nums += num_rx.findall(lines[j])
                if len(nums) >= 4:
                    break
            nums += [None] * (4 - len(nums))
            alpha, beta, up, down = nums[:4]
            vals = [alpha, beta, up, down]

        results.append({
            "Fund Name":               name,
            "Ticker":                  tk,
            "5 Year Alpha":            vals[0],
            "5 Year Beta":             vals[1],
            "5 Year Upside Capture":   vals[2],
            "5 Year Downside Capture": vals[3],
        })

    # 5) Display
    df = pd.DataFrame(results)
    st.session_state["step10_mpt_stats"] = results
    st.dataframe(df)

# === Step 11: Combined MPT Statistics Summary ===
def step11_create_summary(pdf=None):
    import pandas as pd
    import streamlit as st

    st.subheader("Step 11: Combined MPT Statistics Summary")

    # 1) Load your 3‑Yr and 5‑Yr stats from session state
    mpt3 = st.session_state.get("step9_mpt_stats", [])
    mpt5 = st.session_state.get("step10_mpt_stats", [])
    if not mpt3 or not mpt5:
        st.error("❌ Missing MPT stats. Run Steps 9 & 10 first.")
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

# === Step 12: Extract “FUND FACTS” & Its Table Details in One Go ===
def step12_process_fund_facts(pdf):
    import re
    import streamlit as st
    import pandas as pd

    st.subheader("Step 12: Extract Fund Facts Details")

    fs_start   = st.session_state.get("factsheets_page")
    factsheets = st.session_state.get("fund_factsheets_data", [])
    if not fs_start or not factsheets:
        st.error("❌ Run Step 6 first to populate your factsheet pages.")
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


# === Step 13: Extract Risk‑Adjusted Returns Metrics ===
def step13_process_risk_adjusted_returns(pdf):
    import re
    import streamlit as st
    import pandas as pd

    st.subheader("Step 13: Extract Risk‑Adjusted Returns Details")

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

# === Step 14: Extract Peer Risk‑Adjusted Return Ranks ===
def step14_extract_peer_risk_adjusted_return_rank(pdf):
    import re
    import streamlit as st
    import pandas as pd

    st.subheader("Step 14: Peer Risk-Adjusted Return Rank")

    factsheets = st.session_state.get("fund_factsheets_data", [])
    if not factsheets:
        st.error("❌ Run Step 6 first to populate your factsheet pages.")
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

#-------------------------------------------------------------------------------------------
#=== Step 15: Selected Funds ===
def step15_display_selected_fund():
    import streamlit as st
    import pandas as pd

    st.subheader("Step 15: View Single Fund Details")

    # 1) Gather list of fund names from one of the step tables
    #    (we assume every step writes a list/dict keyed by fund name into session_state)
    peer = st.session_state.get("step14_peer_rank_table", [])
    if not peer:
        st.error("❌ Run through Step 14 first to populate data.")
        return

    fund_names = [r["Fund Name"] for r in peer]
    fund_choice = st.selectbox("Select a fund:", fund_names)

    # 2) helper to filter a table/list of dicts by Fund Name
    def lookup(key):
        tbl = st.session_state.get(key, [])
        if isinstance(tbl, pd.DataFrame):
            df = tbl
        else:
            df = pd.DataFrame(tbl)
        if "Fund Name" in df.columns:
            return df[df["Fund Name"] == fund_choice]
        return df  # fallback

    # 3) Display each step’s data for the chosen fund
    st.markdown("**Page 1 extraction:**")
    st.write(lookup("step1_page1_data"))

    st.markdown("**Table of Contents (Step 2):**")
    st.write(lookup("step2_toc_entries"))

    st.markdown("**Scorecard (Step 3):**")
    st.write(lookup("step3_scorecard_data"))

    st.markdown("**IPS Screening (Step 4):**")
    st.write(lookup("step4_ips_results"))

    st.markdown("**Fund Performance (Step 5):**")
    st.write(lookup("step5_performance_data"))

    st.markdown("**Fund Factsheets (Step 6):**")
    st.write(lookup("step6_factsheets_data"))

    st.markdown("**Annualized Returns (Step 7):**")
    st.write(lookup("step7_annual_returns"))

    st.markdown("**Calendar Year Returns (Step 8.5):**")
    st.write(lookup("step8_5_calendar_returns"))

    st.markdown("**MPT Statistics (3Yr & 5Yr) (Steps 9.5 & 10.5):**")
    st.write(lookup("step9_5_mpt3yr"))
    st.write(lookup("step10_5_mpt5yr"))

    st.markdown("**Combined MPT Summary (Step 11):**")
    st.write(lookup("step11_mpt_summary"))

    st.markdown("**Fund Facts (Step 12):**")
    st.write(lookup("step12_fund_facts"))

    st.markdown("**Risk‑Adjusted Returns (Step 13):**")
    st.write(lookup("step13_risk_adjusted_returns"))

    st.markdown("**Peer Risk‑Adjusted Return Rank (Step 14):**")
    st.write(lookup("step14_peer_rank_table"))

# --- In your main app runner, call it:
step15_display_selected_fund()

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

        # Step 9: Match Tickers
        with st.expander("Step 9: Match Tickers in Risk Analysis (3Yr)", expanded=False):
            step9_match_risk_tickers(pdf)

        # Step 9.5: Extract MPT Statistics (3Yr)
        with st.expander("Step 9.5: Extract MPT Statistics (3Yr)", expanded=False):
            step9_extract_mpt_statistics(pdf)

        # Step 10: Match Tickers
        with st.expander("Step 10: Match Tickers in Risk Analysis (5Yr)", expanded=False):
            step10_match_risk_tickers(pdf)

        # Step 10.5: Extract Extract MPT Statistics (5Yr)
        with st.expander("Step 10.5: Extract MPT Statistics (5Yr)", expanded=False):
            step10_extract_mpt_statistics(pdf)

        # Step 11: MPT Statistics Summary
        with st.expander("Step 11: Combined MPT Statistics Summary", expanded=False):
            step11_create_summary()
            
        # Step 12: Find Factsheet Sub‑Headings
        with st.expander("Step 12: Fund Facts ", expanded=False):
            step12_process_fund_facts(pdf)

        # Step 13: Risk Adjusted Returns
        with st.expander("Step 13: Risk‑Adjusted Returns", expanded=False):
            step13_process_risk_adjusted_returns(pdf)

        # Step 14: Peer Risk-Adjusted Return Rank
        with st.expander("Step 14: Peer Risk‑Adjusted Return Rank", expanded=False):
            step14_extract_peer_risk_adjusted_return_rank(pdf)

        # Step 15
        with st.expander("Step 15: Display Selected Fund", expanded=False):
            step15_display_selected_fund(pdf)

if __name__ == "__main__":
    run()

