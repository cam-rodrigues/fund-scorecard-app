import streamlit as st
import pdfplumber
import re
import pandas as pd

# --- Utility: Extract Scorecard Fund Blocks ---
def extract_scorecard_blocks(pdf, scorecard_page):
    """
    Extract all fund blocks and metrics from the scorecard section, starting at scorecard_page.
    Returns a list of dicts: [{Fund Name, Metrics:[{Metric, Status, Info}, ...]}, ...]
    """
    pages = []
    for p in pdf.pages[scorecard_page-1:]:
        txt = p.extract_text() or ""
        pages.append(txt)
    lines = "\n".join(pages).splitlines()

    metric_labels = [
        "Manager Tenure", "Excess Performance (3Yr)", "Excess Performance (5Yr)",
        "Peer Return Rank (3Yr)", "Peer Return Rank (5Yr)", "Expense Ratio Rank",
        "Sharpe Ratio Rank (3Yr)", "Sharpe Ratio Rank (5Yr)", "R-Squared (3Yr)",
        "R-Squared (5Yr)", "Sortino Ratio Rank (3Yr)", "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (3Yr)", "Tracking Error Rank (5Yr)"
    ]

    fund_blocks = []
    fund_name = None
    metrics = []
    for line in lines:
        if not any(metric in line for metric in metric_labels) and line.strip():
            if fund_name and metrics:
                fund_blocks.append({"Fund Name": fund_name, "Metrics": metrics})
            fund_name = line.strip()
            fund_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed on watchlist for not meeting .* out of 14 criteria)", "", fund_name).strip()
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

# --- Conversion: Scorecard → IPS Investment Criteria ---
def scorecard_to_ips(fund_blocks):
    """
    Given a list of fund_blocks with 14 scorecard metrics each,
    returns a DataFrame mapping each fund to 11 IPS Investment Criteria, as per rules.
    """
    metrics_order = [
        "Manager Tenure",               # 1
        "Excess Performance (3Yr)",     # 2
        "Excess Performance (5Yr)",     # 3
        "Peer Return Rank (3Yr)",       # 4
        "Peer Return Rank (5Yr)",       # 5
        "Expense Ratio Rank",           # 6
        "Sharpe Ratio Rank (3Yr)",      # 7
        "Sharpe Ratio Rank (5Yr)",      # 8
        "R-Squared (3Yr)",              # 9
        "R-Squared (5Yr)",              # 10
        "Sortino Ratio Rank (3Yr)",     # 11
        "Sortino Ratio Rank (5Yr)",     # 12
        "Tracking Error Rank (3Yr)",    # 13
        "Tracking Error Rank (5Yr)",    # 14
    ]
    # Indices (0-based) for each IPS, for Active & Passive funds
    active_map  = [0,1,3,6,10,2,4,7,11,5,None]
    passive_map = [0,8,3,6,12,9,4,7,13,5,None]
    ips_labels = [f"IPS Investment Criteria {i+1}" for i in range(11)]

    ips_results = []
    for fund in fund_blocks:
        fund_name = fund["Fund Name"]
        is_passive = "index" in fund_name.lower()  # Customize as needed
        metrics = fund["Metrics"]
        # Get status list in order
        scorecard_status = []
        for label in metrics_order:
            found = next((m for m in metrics if m["Metric"] == label), None)
            scorecard_status.append(found["Status"] if found else None)
        idx_map = passive_map if is_passive else active_map
        # Build IPS statuses
        ips_status = []
        for i, m_idx in enumerate(idx_map):
            if m_idx is not None:
                status = scorecard_status[m_idx]
                ips_status.append(status)
            else:
                ips_status.append("Pass")
        review_fail = sum(1 for status in ips_status if status in ["Review","Fail"])
        if review_fail >= 6:
            watch_status = "Formal Watch"
        elif review_fail >= 5:
            watch_status = "Informal Watch"
        else:
            watch_status = "No Watch"
        row = {
            "Fund Name": fund_name,
            "Fund Type": "Passive" if is_passive else "Active",
            **{ips_labels[i]: ips_status[i] for i in range(11)},
            "IPS Watch Status": watch_status,
        }
        ips_results.append(row)
    return pd.DataFrame(ips_results)

# --- Streamlit App ---
def main():
    st.title("Fidsync: Scorecard ➔ IPS Investment Criteria")
    st.markdown("Upload your MPI PDF and view the IPS screening for all funds, based on the official scorecard-to-IPS conversion logic.")

    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        st.info("Please upload your MPI PDF file.")
        return

    with pdfplumber.open(uploaded) as pdf:
        # Attempt to auto-find the Fund Scorecard page from Table of Contents
        toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        sc_match = re.search(r"Fund Scorecard\s+(\d{1,3})", toc_text or "")
        scorecard_page = int(sc_match.group(1)) if sc_match else 3  # fallback to page 3 if not found

        st.info(f"Using Scorecard page: {scorecard_page}")

        # Extract scorecard blocks
        fund_blocks = extract_scorecard_blocks(pdf, scorecard_page)
        if not fund_blocks:
            st.error("Could not extract fund scorecard blocks. Check the PDF and page number.")
            return

        # Convert to IPS Investment Criteria
        df_ips = scorecard_to_ips(fund_blocks)

        st.header("Scorecard ➔ IPS Investment Criteria Table")
        st.dataframe(df_ips, use_container_width=True)

        # Optional: download as CSV
        st.download_button(
            "Download IPS Screening Table as CSV",
            data=df_ips.to_csv(index=False),
            file_name="ips_screening_table.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
