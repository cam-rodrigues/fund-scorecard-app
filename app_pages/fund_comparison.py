import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# === Extract Performance Metrics from MPI PDF ===
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

# === Clean Bar Chart ===
def plot_bar_chart(df, metric):
    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(df.index, df[metric], color="#4B89DC", width=0.5)

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

# === Heatmap ===
def plot_heatmap(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(df, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, ax=ax, cbar=True)
    ax.set_title("Fund Performance Heatmap")
    plt.xticks(rotation=15)
    return fig

# === Streamlit App Runner ===
def run():
    st.set_page_config(page_title="FidSync Beta - Fund Comparison", layout="wide")
    st.title("📊 Fund Performance Comparison")

    uploaded_pdf = st.file_uploader("Upload MPI-style PDF", type=["pdf"])
    if not uploaded_pdf:
        st.stop()

    with st.spinner("Extracting fund data..."):
        df = extract_fund_performance(uploaded_pdf)

    if df.empty:
        st.error("No fund performance data found.")
        st.stop()

    selected_funds = st.multiselect("Select funds to compare:", df["Fund"].unique())
    if not selected_funds:
        st.warning("Select at least one fund to display comparison.")
        st.stop()

    subset = df[df["Fund"].isin(selected_funds)].set_index("Fund")

    st.subheader("🧾 Raw Performance Table")
    st.dataframe(subset.style.format("{:.2f}"))

    if len(subset) > 1:
        st.subheader("📈 Metric-by-Metric Bar Charts")
        for col in subset.columns:
            fig = plot_bar_chart(subset, col)
            st.pyplot(fig)

        if st.checkbox("Show heatmap instead of bar charts"):
            st.subheader("🌡️ Fund Performance Heatmap")
            fig = plot_heatmap(subset)
            st.pyplot(fig)
    else:
        st.info("Charts will appear once more than one fund is selected.")
