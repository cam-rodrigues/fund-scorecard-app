import streamlit as st
import pdfplumber
import re
import pandas as pd

# --- Utility: Extract Scorecard Fund Blocks ---
def extract_scorecard_blocks(pdf, scorecard_page):
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
def scorecard_to_ips(fund_blocks, fund_types):
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

    ips_results = []
    raw_results = []
    for fund in fund_blocks:
        fund_name = fund["Fund Name"]
        fund_type = fund_types.get(fund_name, "Passive" if "index" in fund_name.lower() else "Active")
        metrics = fund["Metrics"]
        scorecard_status = []
        for label in metrics_order:
            found = next((m for m in metrics if m["Metric"] == label), None)
            scorecard_status.append(found["Status"] if found else None)
        idx_map = passive_map if fund_type == "Passive" else active_map
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
        def iconify(status):
            if status == "Pass":
                return "✅"
            elif status in ("Review", "Fail"):
                return "❌"
            return ""
        row = {
            "Fund Name": fund_name,
            "Fund Type": fund_type,
            **{ips_labels[i]: iconify(ips_status[i]) for i in range(11)},
            "IPS Watch Status": watch_status,
        }
        ips_results.append(row)
        raw_results.append({
            "Fund Name": fund_name,
            "Fund Type": fund_type,
            **{ips_labels[i]: ips_status[i] for i in range(11)},
            "IPS Watch Status": watch_status,
        })
    df_icon = pd.DataFrame(ips_results)
    df_raw  = pd.DataFrame(raw_results)
    return df_icon, df_raw

# --- Streamlit App ---
def main():
    st.title("Fidsync: Scorecard ➔ IPS Investment Criteria")
    st.markdown(
        "Upload your MPI PDF and set each fund as Active or Passive for custom IPS screening. "
        "Green check = Pass, Red X = Review/Fail."
    )

    uploaded = st.file_uploader("Upload MPI PDF", type="pdf")
    if not uploaded:
        st.info("Please upload your MPI PDF file.")
        return

    with pdfplumber.open(uploaded) as pdf:
        toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        sc_match = re.search(r"Fund Scorecard\s+(\d{1,3})", toc_text or "")
        scorecard_page = int(sc_match.group(1)) if sc_match else 3  # fallback to page 3 if not found

        st.info(f"Using Scorecard page: {scorecard_page}")

        fund_blocks = extract_scorecard_blocks(pdf, scorecard_page)
        if not fund_blocks:
            st.error("Could not extract fund scorecard blocks. Check the PDF and page number.")
            return

        # -- "Right sidebar" using columns: left = table, right = selectors --
        left, right = st.columns([3, 1], gap="large")

        # Persist fund type selection
        if "fund_types" not in st.session_state:
            st.session_state["fund_types"] = {
                fund["Fund Name"]: "Passive" if "index" in fund["Fund Name"].lower() else "Active"
                for fund in fund_blocks
            }

        with right:
            st.markdown("### Fund Type (Active/Passive)")
            for fund in fund_blocks:
                name = fund["Fund Name"]
                current_type = st.session_state["fund_types"].get(name, "Passive" if "index" in name.lower() else "Active")
                selected_type = st.radio(
                    label=name,
                    options=["Active", "Passive"],
                    index=0 if current_type == "Active" else 1,
                    key=f"ftype_{name}",
                )
                st.session_state["fund_types"][name] = selected_type

        # Do IPS conversion with current user settings
        df_icon, df_raw = scorecard_to_ips(fund_blocks, st.session_state["fund_types"])

        with left:
            st.header("Scorecard ➔ IPS Investment Criteria Table")
            st.dataframe(df_icon, use_container_width=True)

            st.download_button(
                "Download IPS Screening Table as CSV",
                data=df_raw.to_csv(index=False),
                file_name="ips_screening_table.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    main()
