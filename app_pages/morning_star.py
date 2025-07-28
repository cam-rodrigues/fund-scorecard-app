import re
import streamlit as st
import pdfplumber
import pandas as pd

# === Utility: Extract Split by Two-or-More Spaces ===
def split_cols(line: str) -> list[str]:
    return re.split(r"\s{2,}", line.strip())

# === Step 1: Overview / Page 1 ===
def process_overview(page):
    text = page.extract_text() or ""
    lines = text.splitlines()
    # locate 'Overview' header
    try:
        idx = lines.index('Overview')
    except ValueError:
        st.error("❌ 'Overview' section not found on page 1.")
        return
    # header keys and values
    header_line = lines[idx+1]
    value_line  = lines[idx+2]
    keys = split_cols(header_line)
    vals = split_cols(value_line)
    overview = dict(zip(keys, vals))

    st.subheader('Step 1: Overview / Page 1')
    for k, v in overview.items():
        st.write(f"- {k}: {v}")

    st.session_state['overview'] = overview

# === Step 2: Performance Summary ===
def process_performance(pdf):
    st.subheader('Step 2: Performance Summary')
    # gather lines after finding 'Returns Annual'
    lines = []
    recording = False
    for page in pdf.pages:
        text = page.extract_text() or ''
        for ln in text.splitlines():
            if recording:
                lines.append(ln)
            if ln.strip().startswith('Returns Annual'):
                recording = True
        if recording and len(lines) > 20:
            break

    if not lines:
        st.error("❌ 'Returns Annual' section not found.")
        return
    # first line: year labels
    year_line = lines[0]
    # match years or YTD
    years = re.findall(r'20\d{2}|YTD', year_line)

    # each of Investment, Category, Index
    data = {}
    for label in ['Investment', 'Category', 'Index']:
        if label in lines:
            i = lines.index(label)
            vals_line = lines[i+1] if i+1 < len(lines) else ''
            vals = re.findall(r'-?\d+\.?\d*', vals_line)
            # ensure length matches years
            vals = vals[:len(years)] + [None] * (len(years) - len(vals))
        else:
            vals = [None] * len(years)
        data[label] = vals

    # build DataFrame: rows=labels, cols=years
    df = pd.DataFrame(data, index=years).T
    st.dataframe(df, use_container_width=True)
    st.session_state['performance'] = df

# === Step 3: Top Holdings ===
def process_holdings(pdf):
    st.subheader('Step 3: Top Holdings')
    # placeholder: not yet implemented
    st.write('Holdings parsing not yet implemented.')

# === Step 4: Risk Metrics ===
def process_risk_metrics(pdf):
    st.subheader('Step 4: Risk Metrics')
    # placeholder: not yet implemented
    st.write('Risk-metric parsing not yet implemented.')

# === Main App ===
def run():
    st.title('Morningstar Report Reader')
    st.write('Upload Morningstar PDF')
    uploaded = st.file_uploader('', type='pdf')
    if not uploaded:
        return
    with pdfplumber.open(uploaded) as pdf:
        process_overview(pdf.pages[0])
        process_performance(pdf)
        process_holdings(pdf)
        process_risk_metrics(pdf)

if __name__ == '__main__':
    run()
