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
def extract_scorecard(pdf, start_page, total_declared=None):
    lines = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ''
        if 'Fund Scorecard' in txt:
            lines.extend(txt.splitlines())
        else:
            break
    # find metrics
    idx = next((i for i,l in enumerate(lines) if 'Criteria Threshold' in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    blocks = []
    name = None
    metrics = []
    for i, line in enumerate(lines):
        m = re.match(r'^(.*?)\s+(Pass|Review)\s+(.+)$', line.strip())
        if not m:
            continue
        metric, status, info = m.groups()
        if metric == 'Manager Tenure':
            if name:
                blocks.append({'Fund Name': name, **{m['Metric']: m['Info'] for m in metrics}})
            # find name above
            prev = next((l for l in reversed(lines[:i]) if l.strip()), '')
            name = prev.strip()
            metrics = []
        if name is not None:
            metrics.append({'Metric': metric, 'Status': status, 'Info': info.strip()})
    if name:
        blocks.append({'Fund Name': name, **{m['Metric']: m['Info'] for m in metrics}})
    return pd.DataFrame(blocks)

# === Step 2: IPS Screening ===
def compute_ips(df_scorecard):
    # define IPS criteria functions
    def tenure_ok(x): return float(re.search(r'(\d+\.?\d*)', x).group(1)) >= 3
    df = df_scorecard.copy()
    # assume df has Manager Tenure column
    df['IPS Pass'] = df['Manager Tenure'].apply(lambda x: tenure_ok(x))
    # additional IPS logic can be expanded as needed
    return df

# === Step 3: Extract Tickers ===
def extract_tickers(pdf, start_page, fund_names):
    # extract lines
    lines = []
    text_block = ''
    for p in pdf.pages[start_page-1:]:
        text = p.extract_text() or ''
        text_block += text + '\n'
        lines.extend(text.splitlines())
    mapping = {}
    for ln in lines:
        m = re.match(r'(.+?)\s+([A-Z]{1,5})$', ln.strip())
        if m:
            raw, tkr = m.groups()
            norm = re.sub(r'[^A-Za-z0-9 ]+', '', raw).strip().lower()
            mapping[norm] = tkr
    tickers = {}
    for name in fund_names:
        norm = re.sub(r'[^A-Za-z0-9 ]+', '', name).strip().lower()
        tickers[name] = next((v for k,v in mapping.items() if k.startswith(norm)), None)
    return pd.DataFrame([{'Fund Name': k, 'Ticker': v} for k,v in tickers.items()])

# === Main App ===
def run():
    st.title('Fund Metrics Extractor')
    uploaded = st.file_uploader('Upload MPI PDF', type='pdf')
    if not uploaded:
        return
    with pdfplumber.open(uploaded) as pdf:
        # parse TOC pages 1-3
        toc_text = ''.join((pdf.pages[i].extract_text() or '') for i in range(min(3, len(pdf.pages))))
        pages = parse_toc(toc_text)
        sc_page = pages['scorecard']
        perf_page = pages['performance']
        if sc_page:
            df_score = extract_scorecard(pdf, sc_page)
            st.subheader('Scorecard Metrics')
            st.dataframe(df_score)
        else:
            st.error('Scorecard page not found')

        if sc_page:
            df_ips = compute_ips(df_score)
            st.subheader('IPS Screening Results')
            st.dataframe(df_ips)
        if perf_page and sc_page:
            names = df_score['Fund Name'].tolist()
            df_tkr = extract_tickers(pdf, perf_page, names)
            st.subheader('Extracted Tickers')
            st.dataframe(df_tkr)

if __name__ == '__main__':
    run()
