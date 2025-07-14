import streamlit as st
import pdfplumber
import pandas as pd
import numpy as np
import re
from datetime import datetime
from io import BytesIO

from utils.export.export_client_docx import export_client_docx
from utils.export.export_internal_docx import export_internal_docx
from utils.export.export_pdf import export_pdf

# === Extract Fund Performance ===
def extract_fund_performance(pdf_file):
    performance_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text or "Fund Performance: Current vs." not in text:
                continue
            lines = text.split("\n")
            fund_name = None
            for line in lines:
                if re.search(r"[A-Z]{4,6}X", line):
                    fund_name = line.strip()
                    continue
                if fund_name and re.search(r"[-+]?\d+\.\d+", line):
                    numbers = re.findall(r"[-+]?\d+\.\d+", line)
                    if len(numbers) >= 6:
                        performance_data.append({
                            "Fund": fund_name,
                            "QTD": float(numbers[0]),
                            "YTD": float(numbers[1]),
                            "1 Yr": float(numbers[2]),
                            "3 Yr": float(numbers[3]),
                            "5 Yr": float(numbers[4]),
                            "10 Yr": float(numbers[5]),
                        })
                        fund_name = None
    return pd.DataFrame(performance_data)

# === Helpers ===
def enhance_with_benchmark(df):
    benchmark = {
        "Fund": "S&P 500 (Benchmark)",
        "QTD": 2.00, "YTD": 6.00, "1 Yr": 12.00, "3 Yr": 8.00, "5 Yr": 10.00, "10 Yr": 10.50
    }
    df = pd.concat([df, pd.DataFrame([benchmark])], ignore_index=True)
    np.random.seed(42)
    df["Volatility (%)"] = np.round(np.random.uniform(9, 18, len(df)), 2)
    df["Sharpe Ratio"] = np.round(np.random.uniform(0.4, 1.2, len(df)), 2)
    return df

def extract_clean_name_ticker_date(full_name):
    match = re.search(r"^(.*?)([A-Z]{5})\s.*?(\d{2}/\d{2}/\d{4})", full_name)
    if match:
        name, ticker, date = match.groups()
        return f"{name.strip()} ({ticker})", date
    return full_name, None

def style_scorecard(df):
    styled = df.style.format("{:.2f}")
    for col in df.columns[:-2]:
        styled = styled.background_gradient(cmap="RdYlGn", axis=0, subset=[col])
    return styled

def generate_summary(df):
    df = df.copy()
    if df.index.name == "Fund":
        df.reset_index(inplace=True)
    if "S&P 500 (Benchmark)" not in df["Fund"].values:
        return "_No comparable benchmark available._"
    benchmark = df[df["Fund"] == "S&P 500 (Benchmark)"].iloc[0]
    others = df[df["Fund"] != "S&P 500 (Benchmark)"]
    trailing = ["QTD", "YTD", "1 Yr", "3 Yr", "5 Yr", "10 Yr"]
    if others.empty:
        return "_No comparable fund data available._"
    beat_counts = (others[trailing] > benchmark[trailing]).sum(axis=1)
    avg_returns = others[trailing].mean(axis=1)
    top_beat = others.iloc[beat_counts.idxmax()]
    top_avg = others.iloc[avg_returns.idxmax()]
    low_avg = others.iloc[avg_returns.idxmin()]
    beat_name, _ = extract_clean_name_ticker_date(top_beat["Fund"])
    top_name, _ = extract_clean_name_ticker_date(top_avg["Fund"])
    low_name, _ = extract_clean_name_ticker_date(low_avg["Fund"])
    beat_count = beat_counts.max()
    return f"""**Summary**  
- Fund that outperformed benchmark most: **{beat_name}** ({beat_count} of 6 periods)  
- Top average return: **{top_name}**  
- Lowest performer: **{low_name}**"""

def generate_proposal_text(df):
    trailing_cols = ["QTD", "YTD", "1 Yr", "3 Yr", "5 Yr", "10 Yr"]
    main_funds = df[df["Fund"] != "S&P 500 (Benchmark)"].copy()
    if main_funds.empty:
        return "<i>No valid funds available for proposal generation.</i>"
    benchmark = df[df["Fund"] == "S&P 500 (Benchmark)"].iloc[0]
    main_funds["Avg Return"] = main_funds[trailing_cols].mean(axis=1)
    main_funds["Beats Benchmark"] = (main_funds[trailing_cols] > benchmark[trailing_cols]).sum(axis=1)
    ranked = main_funds.sort_values(["Avg Return", "Sharpe Ratio"], ascending=False)
    top_fund = ranked.iloc[0]
    runner_up = ranked.iloc[1] if len(ranked) > 1 else None
    top_name, top_date = extract_clean_name_ticker_date(top_fund["Fund"])
    proposal = f"""
<h3 style='margin-bottom:0.5rem;'>Proposal Recommendation</h3>
<b>Primary Candidate:</b><br>
<b>{top_name}</b><br>
<em>Inception Date: {top_date}</em>
<ul>
  <li><b>Average Return:</b> {top_fund['Avg Return']:.2f}%</li>
  <li><b>Sharpe Ratio:</b> {top_fund['Sharpe Ratio']}</li>
  <li><b>Volatility:</b> {top_fund['Volatility (%)']}%</li>
  <li><b>Outperformed Benchmark:</b> {top_fund['Beats Benchmark']} of 6 periods</li>
</ul>
"""
    if runner_up is not None:
        runner_name, runner_date = extract_clean_name_ticker_date(runner_up["Fund"])
        proposal += f"""
<br><b>Secondary Consideration:</b><br>
<b>{runner_name}</b><br>
<em>Inception Date: {runner_date}</em>
<ul>
  <li><b>Average Return:</b> {runner_up['Avg Return']:.2f}%</li>
  <li><b>Sharpe Ratio:</b> {runner_up['Sharpe Ratio']}</li>
  <li><b>Volatility:</b> {runner_up['Volatility (%)']}%</li>
  <li><i>May be more appropriate for moderate-risk investors</i></li>
</ul>
"""
    return proposal

# === Streamlit App ===
def run():
    st.set_page_config(page_title="FidSync Beta - Fund Comparison", layout="wide")
    st.title("Proposal Generator")

    # Step tracker state
    if "step" not in st.session_state:
        st.session_state.step = 1

    # Sidebar progress indicator
    st.sidebar.markdown("### Progress")
    steps = [
        "Step 1: Upload PDF",
        "Step 2: Select Funds",
        "Step 3: Choose Format",
        "Step 4: Review Output",
        "Step 5: Export"
    ]
    for i, label in enumerate(steps, start=1):
        prefix = "✅ " if i < st.session_state.step else "➡️ " if i == st.session_state.step else "🔒 "
        st.sidebar.markdown(f"{prefix} {label}")

    # === Step 1: Upload PDF ===
    st.header("Step 1: Upload MPI PDF")
    uploaded_pdf = st.file_uploader("Upload your MPI-style PDF", type=["pdf"])
    if not uploaded_pdf:
        st.stop()
    st.session_state.step = 2

    # === Step 2: Extract and Select ===
    with st.spinner("Reading uploaded PDF..."):
        df = extract_fund_performance(uploaded_pdf)

    if df.empty:
        st.error("No fund performance data found.")
        st.stop()

    st.header("Step 2: Select Funds")
    fund_choices = df["Fund"].unique()
    select_all = st.checkbox("Select All Funds", value=False)
    deselect_all = st.checkbox("Deselect All", value=False)
    default_selection = list(fund_choices) if select_all and not deselect_all else []
    selected = st.multiselect("Pick the funds to analyze", fund_choices, default=default_selection)

    if not selected:
        st.warning("Please select at least one fund.")
        st.stop()
    st.session_state.step = 3

    # === Step 3: Choose Export Format ===
    st.header("Step 3: Choose Export Format")
    template = st.selectbox("Choose export format:", [
        "Client-facing DOCX",
        "Internal DOCX",
        "PDF Summary"
    ])
    st.session_state.step = 4

    # === Step 4: Show Results ===
    enhanced_df = enhance_with_benchmark(df[df["Fund"].isin(selected)])
    summary = generate_summary(enhanced_df)
    proposal = generate_proposal_text(enhanced_df)

    st.header("Step 4: Review Output")
    
    st.subheader("### Fund Summary")
    st.markdown(summary)

    st.subheader("### Scorecard")
    st.dataframe(style_scorecard(enhanced_df.set_index("Fund")), use_container_width=True)

    st.subheader("### Recomendation")
    st.markdown(proposal, unsafe_allow_html=True)
    st.session_state.step = 5

    # === Step 5: Export ===
    st.header("Step 5: Export")
    buffer = BytesIO()
    if template == "Client-facing DOCX":
        export_client_docx(enhanced_df, proposal, buffer)
        file_name = "Client_Proposal.docx"
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif template == "Internal DOCX":
        export_internal_docx(enhanced_df, proposal, buffer)
        file_name = "Internal_Proposal.docx"
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif template == "PDF Summary":
        export_pdf(summary, proposal, buffer)
        file_name = "Proposal_Summary.pdf"
        mime_type = "application/pdf"

    buffer.seek(0)
    st.download_button(
        label=f"Download {file_name}",
        data=buffer,
        file_name=file_name,
        mime=mime_type
    )
