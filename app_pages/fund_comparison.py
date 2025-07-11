import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# === Extract trailing return performance from MPI PDF ===
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
                # Detect fund name by presence of ticker
                if re.search(r"[A-Z]{4,6}X", line):
                    fund_name = line.strip()
                    continue

                # Extract numeric trailing returns
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

# === Bar chart generator for a single metric ===
def plot_bar_chart(df, metric):
    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(df.index, df[metric], color="#4B89DC", width=0.5)

    # Add labels above each bar
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9)

    ax.set_ylabel(metric)
    ax.set_title(f"{metric} Comparison")
    ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    plt.xticks(rotation=15)
    plt.tight_layout()
    return fig

# === Heatmap for all selected fund metrics ===
def plot_heatmap(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(df, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, ax=ax, cbar=True)
    ax.set_title("Fund Performance Heatmap")
    plt.xticks(rotation=15)
    return fig

# === Streamlit entry point ===
def run():
    st.set_page_config(page_title="FidSync Beta - Fund Comparison", layout="wide")
    st.title("Fund Performance Comparison")

    uploaded_pdf = st.file_uploader("Upload an MPI-style Fund PDF", type=["pdf"])
    if not uploaded_pdf:
        st.stop()

    with st.spinner("Processing file and extracting performance metrics..."):
        df = extract_fund_performance(uploaded_pdf)

    if df.empty:
        st.error("No performance data could be extracted from this file.")
        st.stop()

    selected_funds = st.multiselect("Select funds to compare", df["Fund"].unique())
    if not selected_funds:
        st.warning("Please select at least one fund to proceed.")
        st.stop()

    subset = df[df["Fund"].isin(selected_funds)].set_index("Fund")

    st.markdown("### Performance Table")
    st.dataframe(subset.style.format("{:.2f}"))

    if len(subset) > 1:
        st.markdown("### Performance Charts by Metric")
        for col in subset.columns:
            fig = plot_bar_chart(subset, col)
            st.pyplot(fig)

        st.markdown("---")
        if st.checkbox("Show heatmap view instead of bar charts"):
            st.markdown("### Fund Performance Heatmap")
            fig = plot_heatmap(subset)
            st.pyplot(fig)
    else:
        st.info("Charts require selection of at least two funds.")
