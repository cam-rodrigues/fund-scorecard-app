import pandas as pd
import streamlit as st

# === Color-Coded Scorecard ===
def style_scorecard(df):
    styled = df.style.format("{:.2f}")
    for col in df.columns:
        styled = styled.background_gradient(
            cmap="RdYlGn", axis=0, low=0.2, high=0.8, subset=[col]
        )
    return styled

# === Summary Generator ===
def generate_summary(df):
    avg_returns = df.mean(axis=1)
    top_fund = avg_returns.idxmax()
    worst_fund = avg_returns.idxmin()
    top_avg = avg_returns.max()
    worst_avg = avg_returns.min()

    wins = df.eq(df.max()).sum(axis=1)
    leader = wins.idxmax()

    return f"""**Summary**
- Top performing fund: **{top_fund}** (avg return: {top_avg:.2f}%)
- Lowest performer: **{worst_fund}** (avg return: {worst_avg:.2f}%)
- {leader} outperformed peers in the most categories.
"""

# === Usage in Streamlit (inside your `run()` function)
# Assuming df is your filtered subset with index = fund names
if len(subset) >= 1:
    st.markdown("### Performance Summary")
    st.markdown(generate_summary(subset))

    st.markdown("### Scorecard Table")
    st.dataframe(style_scorecard(subset), use_container_width=True)

    if st.checkbox("Show heatmap view instead"):
        st.markdown("### Performance Heatmap")
        st.dataframe(subset.style.background_gradient(cmap="coolwarm").format("{:.2f}"))

else:
    st.info("Please select at least one fund.")
