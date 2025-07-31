import re
import streamlit as st
import pdfplumber
import pandas as pd

# === Utility: Parse Table of Contents to locate sections ===
def parse_toc(text):
    pages = {}
    patterns = {
        'scorecard': r'Fund Scorecard\s+(\d{1,3})',
        'performance': r'Fund Performance[^\d]*(\d{1,3})'
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text or "")
        pages[key] = int(m.group(1)) if m else None
    return pages

# === Step 1: Extract Scorecard Metrics ===
def extract_scorecard(pdf, start_page):
    lines = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ''
        if 'Fund Scorecard' in txt:
            lines.extend(txt.splitlines())
        else:
            break
    idx = next((i for i,l in enumerate(lines) if 'Criteria Threshold' in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    records = []
    name = None
    metrics = []
    for i, line in enumerate(lines):
        m = re.match(r'^(.*?)\s+(Pass|Review)\s+(.+)$', line.strip())
        if not m:
            continue
        metric, status, info = m.groups()
        if metric == 'Manager Tenure':
            if name:
                rec = {'Fund Name': name}
                for met in metrics:
                    rec[f"{met['Metric']}"] = met['Info']
                records.append(rec)
            prev = next((l for l in reversed(lines[:i]) if l.strip()), '')
            name = prev.strip()
            metrics = []
        if name:
            metrics.append({'Metric': metric, 'Status': status, 'Info': info.strip()})
    if name:
        rec = {'Fund Name': name}
        for met in metrics:
            rec[f"{met['Metric']}"] = met['Info']
        records.append(rec)
    return pd.DataFrame(records)

# === Step 2: IPS Screening ===
def compute_ips(df_score):
    def tenure_ok(x):
        m = re.search(r'(\d+\.?\d*)', str(x))
        return float(m.group(1)) >= 3 if m else False
    df = df_score.copy()
    df['IPS Pass'] = df['Manager Tenure'].apply(tenure_ok)
    return df

# === Step 3: Extract Tickers using Fund Performance logic ===
def extract_tickers(pdf, start_page, fund_names):
    # Gather text and lines
    perf_text = ''
    lines = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ''
        perf_text += txt + '\n'
        lines.extend(txt.splitlines())

    # First-pass mapping: name prefix → ticker
    mapping = {}
    for ln in lines:
        m = re.match(r'(.+?)\s+([A-Z]{1,5})$', ln.strip())
        if m:
            raw, tkr = m.groups()
            norm = re.sub(r'[^A-Za-z0-9 ]+', '', raw).strip().lower()
            mapping[norm] = tkr

    tickers = {}
    for name in fund_names:
        norm_expected = re.sub(r'[^A-Za-z0-9 ]+', '', name).strip().lower()
        found = next((t for k, t in mapping.items() if k.startswith(norm_expected)), None)
        tickers[name] = found

    # Fallback: collect all uppercase codes
    if sum(1 for v in tickers.values() if v) < len(fund_names):
        all_codes = re.findall(r'\b([A-Z]{1,5})\b', perf_text)
        seen = []
        for c in all_codes:
            if c not in seen:
                seen.append(c)
        for i, name in enumerate(fund_names):
            if not tickers[name] and i < len(seen):
                tickers[name] = seen[i]

    return pd.DataFrame([{'Fund Name': n, 'Ticker': tickers.get(n)} for n in fund_names])

# === Main App ===
def run():
    st.title('Fund Metrics Extractor')
    uploaded = st.file_uploader('Upload MPI PDF', type='pdf')
    if not uploaded:
        return
    with pdfplumber.open(uploaded) as pdf:
        toc_text = ''.join((pdf.pages[i].extract_text() or '') for i in range(min(3, len(pdf.pages))))
        pages = parse_toc(toc_text)
        sc_page = pages.get('scorecard')
        perf_page = pages.get('performance')

        if not sc_page:
            st.error('Fund Scorecard page not found in TOC')
            return
        df_score = extract_scorecard(pdf, sc_page)
        st.subheader('Scorecard Metrics')
        st.dataframe(df_score)

        df_ips = compute_ips(df_score)
        st.subheader('IPS Screening Results')
        st.dataframe(df_ips)

        if perf_page:
            names = df_score['Fund Name'].tolist()
            df_tkr = extract_tickers(pdf, perf_page, names)
            st.subheader('Extracted Tickers')
            st.dataframe(df_tkr)
        else:
            st.error('Fund Performance page not found in TOC')

if __name__ == '__main__':
    run()
