import streamlit as st
import pdfplumber
import re
import pandas as pd
import yfinance as yf

def infer_fund_type_guess(ticker):
    """Infer 'Active' or 'Passive' based on Yahoo Finance info (name and summary)."""
    try:
        if not ticker:
            return ""
        info = yf.Ticker(ticker).info
        name = (info.get("longName") or info.get("shortName") or "").lower()
        summary = (info.get("longBusinessSummary") or "").lower()
        # Passive if index-related, otherwise Active
        if "index" in name or "index" in summary:
            return "Passive"
        if "track" in summary and "index" in summary:
            return "Passive"
        if "actively managed" in summary or "actively-managed" in summary:
            return "Active"
        if "outperform" in summary or "manager selects" in summary:
            return "Active"
        return ""
    except Exception:
        return ""

def extract_scorecard_blocks(pdf, scorecard_page):
    metric_labels = [
        "Manager Tenure", "Excess Performance (3Yr)", "Excess Performance (5Yr)",
        "Peer Return Rank (3Yr)", "Peer Return Rank (5Yr)", "Expense Ratio Rank",
        "Sharpe Ratio Rank (3Yr)", "Sharpe Ratio Rank (5Yr)", "R-Squared (3Yr)",
        "R-Squared (5Yr)", "Sortino Ratio Rank (3Yr)", "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (3Yr)", "Tracking Error Rank (5Yr)"
    ]
    pages, fund_blocks, fund_name, metrics = [], [], None, []
    for p in pdf.pages[scorecard_page-1:]:
        pages.append(p.extract_text() or "")
    lines = "\n".join(pages).splitlines()
    for line in lines:
        if not any(metric in line for metric in metric_labels) and line.strip():
            if fund_name and metrics:
                fund_blocks.append({"Fund Name": fund_name, "Metrics": metrics})
            fund_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist for not meeting .* out of 14 criteria)", "", line.strip()).strip()
            metrics = []
        for metric in metric_labels:
            if metric in line:
                m = re.match(r"^(.*?)\s+(Pass|Review|Fail)\s*(.*)", line.strip())
                if m:
                    metric_name, status, info = m.groups()
                    metrics.append({"Metric": metric_name, "Status": status, "Info": info.strip()})
    if fund_name and metrics:
        fund_blocks.append({"Fund Name": fund_name, "Metrics": metrics})
    return fund_blocks

def extract_fund_tickers(pdf, performance_page, fund_names, factsheets_page=None):
    end_page = factsheets_page-1 if factsheets_page else len(pdf.pages)
    all_lines, perf_text = [], ""
    for p in pdf.pages[performance_page-1:end_page]:
        txt = p.extract_text() or ""
        perf_text += txt + "\n"
        all_lines.extend(txt.splitlines())
    mapping = {}
    for ln in all_lines:
        m = re.match(r"(.+?)\s+([A-Z]{1,5})$", ln.strip())
        if not m:
            continue
        raw_name, ticker = m.groups()
        norm = re.sub(r'[^A-Za-z0-9 ]+', '', raw_name).strip().lower()
        mapping[norm] = ticker
    tickers = {}
    for name in fund_names:
        norm_expected = re.sub(r'[^A-Za-z0-9 ]+', '', name).strip().lower()
        found = next((t for raw, t in mapping.items() if raw.startswith(norm_expected)), None)
        tickers[name] = found
    total = len(fund_names)
    found_count = sum(1 for t in tickers.values() if t)
    if found_count < total:
        all_tks = re.findall(r'\b([A-Z]{1,5})\b', perf_text)
        seen = []
        for tk in all_tks:
            if tk not in seen:
                seen.append(tk)
        tickers = {name: (seen[i] if i < len(seen) else "") for i, name in enumerate(fund_names)}
    return {k: (v if v else "") for k, v in tickers.items()}

def scorecard_to_ips(fund_blocks, fund_types, tickers):
    metrics_order = [
        "Manager Tenure", "Excess Performance (3Yr)", "Excess Performance (5Yr)",
        "Peer Return Rank (3Yr)", "Peer Return Rank (5Yr)", "Expense Ratio Rank",
        "Sharpe Ratio Rank (3Yr)", "Sharpe Ratio Rank (5Yr)", "R-Squared (3Yr)",
        "R-Squared (5Yr)", "Sortino Ratio Rank (3Yr)", "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (3Yr)", "Tracking Error Rank (5Yr)",
    ]
    active_map  = [0,1,3,6,10,2,4,7,11,5,None]
    passive_map = [0,8,3,6,12,9,4,7,13,5,None]
    ips_labels = [f"IPS Investment Criteria {i+1}" for i in range(11)]
    ips_results, raw_results = [], []
    for fund in fund_blocks:
        fund_name = fund["Fund Name"]
        fund_type = fund_types.get(fund_name, "Passive" if "index" in fund_name.lower() else "Active")
        metrics = fund["Metrics"]
        scorecard_status = [next((m["Status"] for m in metrics if m["Metric"] == label), None) for label in metrics_order]
        idx_map = passive_map if fund_type == "Passive" else active_map
        ips_status = [scorecard_status[m_idx] if m_idx is not None else "Pass" for m_idx in idx_map]
        review_fail = sum(1 for status in ips_status if status in ["Review","Fail"])
        watch_status = "FW" if review_fail >= 6 else "IW" if review_fail >= 5 else "NW"
        def iconify(status): return "✔" if status == "Pass" else "✗" if status in ("Review", "Fail") else ""
        row = {
            "Fund Name": fund_name,
            "Ticker": tickers.get(fund_name, ""),
            "Fund Type": fund_type,
            **{ips_labels[i]: iconify(ips_status[i]) for i in range(11)},
            "IPS Watch Status": watch_status,
        }
        ips_results.append(row)
        raw_results.append({
            "Fund Name": fund_name,
            "Ticker": tickers.get(fund_name, ""),
            "Fund Type": fund_type,
            **{ips_labels[i]: ips_status[i] for i in range(11)},
            "IPS Watch Status": watch_status,
        })
    return pd.DataFrame(ips_results), pd.DataFrame(raw_results)

def watch_status_color(val):
    if val == "FW":
        return "background-color:#f8d7da; color:#c30000; font-weight:600;"
    if val == "IW":
        return "background-color:#fff3cd; color:#B87333; font-weight:600;"
    if val == "NW":
        return "background-color:#d6f5df; color:#217a3e; font-weight:600;"
    return ""

def main():
    st.set_page_config(page_title="IPS Screening")
    st.title("IPS Screening")
    st.markdown(
        '<div class="watch-key">'
        '<span style="background:#d6f5df; color:#217a3e; padding:0.07em 0.55em; border-radius:2px;">NW</span> '
        '(No Watch) &nbsp;'
        '<span style="background:#fff3cd; color:#B87333; padding:0.07em 0.55em; border-radius:2px;">IW</span> '
        '(Informal Watch) &nbsp;'
        '<span style="background:#f8d7da; color:#c30000; padding:0.07em 0.55em; border-radius:2px;">FW</span> '
        '(Formal Watch)</div>', unsafe_allow_html=True
    )

    uploaded = st.file_uploader("Upload MPI PDF", type="pdf", label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)
    if not uploaded:
        st.info("Upload your MPI PDF to begin.")
        st.stop()
    with pdfplumber.open(uploaded) as pdf:
        toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        sc_match = re.search(r"Fund Scorecard\s+(\d{1,3})", toc_text or "")
        perf_match = re.search(r"Fund Performance[^\d]*(\d{1,3})", toc_text or "")
        factsheets_match = re.search(r"Fund Factsheets\s+(\d{1,3})", toc_text or "")
        scorecard_page = int(sc_match.group(1)) if sc_match else 3
        performance_page = int(perf_match.group(1)) if perf_match else scorecard_page + 1
        factsheets_page = int(factsheets_match.group(1)) if factsheets_match else None

        fund_blocks = extract_scorecard_blocks(pdf, scorecard_page)
        fund_names = [fund["Fund Name"] for fund in fund_blocks]
        if not fund_blocks:
            st.error("Could not extract fund scorecard blocks. Check the PDF and page number.")
            st.stop()
        tickers = extract_fund_tickers(pdf, performance_page, fund_names, factsheets_page)

        # --- Fund Type Guess logic (Yahoo guess: always Passive if index detected, else Active) ---
        fund_type_guesses = []
        for name in fund_names:
            guess = ""
            if tickers.get(name):
                guess = infer_fund_type_guess(tickers[name])
            if guess == "Passive":
                fund_type_guesses.append("Passive")
            else:
                fund_type_guesses.append("Active")

        # --- Default logic (index in name → Passive, else Active) ---
        fund_type_defaults = ["Passive" if "index" in n.lower() else "Active" for n in fund_names]

        st.markdown('<b>Edit Fund Type for Screening:</b>', unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.96em; color:#374151; margin-bottom:0.25em;'>"
            "<b>Fund Type Guess:</b> This column is based on Yahoo Finance data. "
            "If the fund name or description mentions 'index' or tracking an index, it's classified as Passive. "
            "Otherwise, it's marked Active. This guess is for convenience only—always confirm with the official fund documentation. "
            "The editable Fund Type column lets you override or accept this guess."
            "</div>",
            unsafe_allow_html=True
        )

        # --- Checkbox for logic choice ---
        use_guess = st.checkbox(
            "Prefill Fund Type with Yahoo Finance guess instead of default (index = Passive, else Active)",
            value=True
        )

        # --- Decide which to use for editable Fund Type column ---
        prefill_fund_type = fund_type_guesses if use_guess else fund_type_defaults

        df_types = pd.DataFrame({
            "Fund Name": fund_names,
            "Ticker": [tickers[name] for name in fund_names],
            "Fund Type Guess": fund_type_guesses,      # read-only
            "Fund Type": prefill_fund_type,            # editable
        })

        edited_types = st.data_editor(
            df_types,
            column_config={
                "Fund Type": st.column_config.SelectboxColumn("Fund Type", options=["Active", "Passive"]),
            },
            disabled=["Fund Name", "Ticker", "Fund Type Guess"],  # Only Fund Type is editable!
            hide_index=True,
            key="data_editor_fundtype",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        fund_types = {row["Fund Name"]: row["Fund Type"] for _, row in edited_types.iterrows()}
        df_icon, df_raw = scorecard_to_ips(fund_blocks, fund_types, tickers)
        st.markdown('<div class="app-card" style="padding:1.2rem 1.2rem 1rem 1.2rem; margin-bottom:0.3rem;">', unsafe_allow_html=True)
        styled = df_icon.style.applymap(watch_status_color, subset=["IPS Watch Status"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.download_button(
            "Download CSV",
            data=df_raw.to_csv(index=False),
            file_name="ips_screening_table.csv",
            mime="text/csv",
        )
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
def run():
    main()
