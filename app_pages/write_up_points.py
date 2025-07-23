import re
import streamlit as st
import pdfplumber
from calendar import month_name

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
    
# === Step 1 & 1.5: Page 1 Extraction ===
def process_page1(text):
    # Report date (quarter‐end or fallback)
    report_date = extract_report_date(text)
    if report_date:
        st.session_state["report_date"] = report_date
        st.success(f"Report Date: {report_date}")
    else:
        st.error("Could not detect report date on page 1.")

    # Total Options
    m = re.search(r"Total Options:\s*(\d+)", text or "")
    st.session_state["total_options"] = int(m.group(1)) if m else None

    # Prepared For
    m = re.search(r"Prepared For:\s*\n(.*)", text or "")
    st.session_state["prepared_for"] = m.group(1).strip() if m else None

    # Prepared By (fallback to Procyon Partners, LLC)
    m = re.search(r"Prepared By:\s*(.*)", text or "")
    pb = m.group(1).strip() if m else ""
    if not pb or "mpi stylus" in pb.lower():
        pb = "Procyon Partners, LLC"
    st.session_state["prepared_by"] = pb

    # Display
    st.subheader("Page 1 Metadata")
    st.write(f"- Total Options: {st.session_state['total_options']}")
    st.write(f"- Prepared For: {st.session_state['prepared_for']}")
    st.write(f"- Prepared By: Procyon Partners, LLC")


# === Step 2: Table of Contents Extraction ===
def process_toc(text):
    """
    Parses the TOC page text to find the start pages for:
      – Fund Performance
      – Fund Scorecard
      – Fund Factsheets
    """
    perf = re.search(r"Fund Performance[^\d]*(\d{1,3})", text or "")
    sc   = re.search(r"Fund Scorecard\s+(\d{1,3})", text or "")
    fs   = re.search(r"Fund Factsheets\s+(\d{1,3})", text or "")

    perf_page = int(perf.group(1)) if perf else None
    sc_page   = int(sc.group(1))   if sc   else None
    fs_page   = int(fs.group(1))   if fs   else None

    st.subheader("Table of Contents Pages")
    st.write(f"- Performance Page: {perf_page}")
    st.write(f"- Scorecard Page:   {sc_page}")
    st.write(f"- Factsheets Page:  {fs_page}")

    st.session_state["performance_page"] = perf_page
    st.session_state["scorecard_page"]   = sc_page
    st.session_state["factsheets_page"]  = fs_page



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

    st.subheader("Step 3.5: Key Details per Metric")
    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            st.write(f"- **{m['Metric']}**: {m['Info'].strip()}")

    st.subheader("Step 3.6: Investment Option Count")
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
    st.subheader("Step 4: IPS Investment Criteria Screening")

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


# === Step 5: Fund Performance Section Extraction (with fallback) ===
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
    st.subheader("Step 5: Extracted Tickers")
    for n, t in tickers.items():
        st.write(f"- {n}: {t or '❌ not found'}")

    # validation
    st.subheader("Step 5.5: Ticker Count Validation")
    found_count = sum(1 for t in tickers.values() if t)
    st.write(f"- Expected tickers: **{total}**")
    st.write(f"- Found tickers:    **{found_count}**")
    if found_count == total:
        st.success("✅ All tickers found.")
    else:
        st.error(f"❌ Missing {total - found_count} ticker(s).")

    # === Step 6: Fund Factsheets Section ===
        
        factsheet_start = st.session_state.get("toc_pages", {}).get("Fund Factsheets")
        total_declared = st.session_state.get("total_options")
        performance_data = st.session_state.get("fund_performance_data", [])
        
        if not factsheet_start:
            st.error("❌ 'Fund Factsheets' page number not found in TOC.")
        else:
            with pdfplumber.open(uploaded_file) as pdf:
                matched_factsheets = []
        
                for i in range(factsheet_start - 1, len(pdf.pages)):
                    page = pdf.pages[i]
                    words = page.extract_words(use_text_flow=True)
                    header_words = [w['text'] for w in words if w['top'] < 100]
        
                    first_line = " ".join(header_words).strip()
                    if not first_line or "Benchmark:" not in first_line or "Expense Ratio:" not in first_line:
                        continue
        
                    ticker_match = re.search(r"\b([A-Z]{5})\b", first_line)
                    ticker = ticker_match.group(1) if ticker_match else ""
        
                    fund_name_raw = first_line.split(ticker)[0].strip() if ticker else ""
        
                    best_score = 0
                    matched_name = ""
                    matched_ticker = ""
        
                    for item in performance_data:
                        ref_name = f"{item['Fund Scorecard Name']} {item['Ticker']}".strip()
                        score = fuzz.token_sort_ratio(f"{fund_name_raw} {ticker}".lower(), ref_name.lower())
                        if score > best_score:
                            best_score = score
                            matched_name = item["Fund Scorecard Name"]
                            matched_ticker = item["Ticker"]
        
                    # === Extract fields ===
                    def extract_field(label, text, stop_at=None):
                        try:
                            start = text.index(label) + len(label)
                            rest = text[start:]
                            if stop_at and stop_at in rest:
                                return rest[:rest.index(stop_at)].strip()
                            return rest.split()[0]
                        except Exception:
                            return ""
        
                    benchmark = extract_field("Benchmark:", first_line, "Category:")
                    category = extract_field("Category:", first_line, "Net Assets:")
                    net_assets = extract_field("Net Assets:", first_line, "Manager Name:")
                    manager = extract_field("Manager Name:", first_line, "Avg. Market Cap:")
                    avg_cap = extract_field("Avg. Market Cap:", first_line, "Expense Ratio:")
                    expense = extract_field("Expense Ratio:", first_line)
        
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
        
            # Remove "first_line" / "Top Line" from display
            df_facts = pd.DataFrame(matched_factsheets)
            st.session_state["fund_factsheets_data"] = matched_factsheets
        
            display_df = df_facts[[
                "Matched Fund Name",
                "Matched Ticker",
                "Benchmark",
                "Category",
                "Net Assets",
                "Manager Name",
                "Avg. Market Cap",
                "Expense Ratio",
                "Matched"
            ]].rename(columns={
                "Matched Fund Name": "Fund Name",
                "Matched Ticker": "Ticker"
            })
            
            st.dataframe(display_df, use_container_width=True)

    
            matched_count = sum(1 for row in matched_factsheets if row["Matched"] == "✅")
            
            if not st.session_state.get("suppress_matching_confirmation", False):
                st.write(f"Matched {matched_count} of {len(matched_factsheets)} factsheet pages.")
            
                if matched_count == total_declared:
                    st.success(f"All {matched_count} funds matched the declared Total Options from Page 1.")
                else:
                    st.error(f"Mismatch: Page 1 declared {total_declared}, but only matched {matched_count}.")



# === Main App ===
def run():
    st.title("MPI Tool — Steps 1 to 6")
    uploaded_file = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded_file:
        return

    with pdfplumber.open(uploaded_file) as pdf:
        # Step 1 & 1.5
        process_page1(pdf.pages[0].extract_text() or "")

        # Step 2
        if len(pdf.pages) > 1:
            process_toc(pdf.pages[1].extract_text() or "")
        else:
            st.warning("Please complete Steps 1–2 first before running Steps 3–4.")
            return

        # Steps 3 & 4 — run but hide their output
        sc_page    = st.session_state.get("scorecard_page")
        total_opts = st.session_state.get("total_options")
        if sc_page is None or total_opts is None:
            st.warning("Please complete Steps 1–2 first before running Steps 3–4.")
            return

        with st.expander("Step 3 (scorecard) – hidden", expanded=False):
            step3_process_scorecard(pdf, sc_page, total_opts)
        with st.expander("Step 4 (IPS screening) – hidden", expanded=False):
            step4_ips_screen()

        # Step 5 & 5.5
        perf_page  = st.session_state.get("performance_page")
        fund_names = [b["Fund Name"] for b in st.session_state.get("fund_blocks", [])]
        if not perf_page or not fund_names:
            st.warning("Please complete Steps 1–3 (including TOC & Scorecard) first.")
            return

        step5_process_performance(pdf, perf_page, fund_names)

        # === Step 6: Fund Factsheets Section ===
        factsheet_start   = st.session_state.get("toc_pages", {}).get("Fund Factsheets")
        total_declared    = st.session_state.get("total_options")
        performance_data  = st.session_state.get("fund_performance_data", [])

        if not factsheet_start:
            st.error("❌ 'Fund Factsheets' page number not found in TOC.")
        else:
            matched_factsheets = []

            for i in range(factsheet_start - 1, len(pdf.pages)):
                page = pdf.pages[i]
                words = page.extract_words(use_text_flow=True)
                header_words = [w["text"] for w in words if w["top"] < 100]

                first_line = " ".join(header_words).strip()
                if not first_line or "Benchmark:" not in first_line or "Expense Ratio:" not in first_line:
                    continue

                # parse ticker & raw name
                ticker_match   = re.search(r"\b([A-Z]{5})\b", first_line)
                ticker         = ticker_match.group(1) if ticker_match else ""
                fund_name_raw  = first_line.split(ticker)[0].strip() if ticker else ""

                # fuzzy‑match back to your performance_data list
                best_score     = 0
                matched_name   = ""
                matched_ticker = ""
                for item in performance_data:
                    ref_name = f"{item['Fund Scorecard Name']} {item['Ticker']}".strip()
                    score    = fuzz.token_sort_ratio(
                        f"{fund_name_raw} {ticker}".lower(),
                        ref_name.lower()
                    )
                    if score > best_score:
                        best_score     = score
                        matched_name   = item["Fund Scorecard Name"]
                        matched_ticker = item["Ticker"]

                # helper to pull out a labeled field
                def extract_field(label, text, stop_at=None):
                    try:
                        start = text.index(label) + len(label)
                        rest  = text[start:]
                        if stop_at and stop_at in rest:
                            return rest[:rest.index(stop_at)].strip()
                        return rest.split()[0]
                    except Exception:
                        return ""

                benchmark   = extract_field("Benchmark:", first_line,    "Category:")
                category    = extract_field("Category:",  first_line,    "Net Assets:")
                net_assets  = extract_field("Net Assets:", first_line,   "Manager Name:")
                manager     = extract_field("Manager Name:", first_line, "Avg. Market Cap:")
                avg_cap     = extract_field("Avg. Market Cap:", first_line, "Expense Ratio:")
                expense     = extract_field("Expense Ratio:", first_line)

                matched_factsheets.append({
                    "Page #":             i + 1,
                    "Parsed Fund Name":   fund_name_raw,
                    "Parsed Ticker":      ticker,
                    "Matched Fund Name":  matched_name,
                    "Matched Ticker":     matched_ticker,
                    "Benchmark":          benchmark,
                    "Category":           category,
                    "Net Assets":         net_assets,
                    "Manager Name":       manager,
                    "Avg. Market Cap":    avg_cap,
                    "Expense Ratio":      expense,
                    "Match Score":        best_score,
                    "Matched":            "✅" if best_score > 20 else "❌"
                })

            # stash & display
            df_facts = pd.DataFrame(matched_factsheets)
            st.session_state["fund_factsheets_data"] = matched_factsheets

            display_df = df_facts[[
                "Matched Fund Name",
                "Matched Ticker",
                "Benchmark",
                "Category",
                "Net Assets",
                "Manager Name",
                "Avg. Market Cap",
                "Expense Ratio",
                "Matched"
            ]].rename(columns={
                "Matched Fund Name": "Fund Name",
                "Matched Ticker":     "Ticker"
            })
            st.dataframe(display_df, use_container_width=True)

            matched_count = sum(1 for row in matched_factsheets if row["Matched"] == "✅")
            if not st.session_state.get("suppress_matching_confirmation", False):
                st.write(f"Matched {matched_count} of {len(matched_factsheets)} factsheet pages.")
                if matched_count == total_declared:
                    st.success(f"All {matched_count} funds matched the declared Total Options from Page 1.")
                else:
                    st.error(f"Mismatch: Page 1 declared {total_declared}, but only matched {matched_count}.")
