import streamlit as st
import pdfplumber
import re
import pandas as pd

# ----- Hide Streamlit branding, menu, footer -----
st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding-top: 2.2rem; padding-bottom: 2rem; max-width: 980px;}
    .app-card {
        background: #f5f7fa;
        border-radius: 1.2rem;
        box-shadow: 0 2px 14px rgba(90,110,160,0.07);
        padding: 2.1rem 2.5rem 2.1rem 2.5rem;
        margin-bottom: 2rem;
    }
    .main-title {
        font-size: 2.1rem !important;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #1c2336;
        margin-bottom: 0.2em;
    }
    .subtle {
        color: #4B5563;
        font-size: 1.07rem;
        margin-bottom: 2em;
    }
    .label-clean {
        font-weight: 500;
        color: #435070;
        font-size: 1.05em;
        margin-top: 0.6em;
    }
    .css-1kyxreq {padding-bottom: 0px !important;} /* tighter table */
    .stDataFrame th, .stDataFrame td {padding: 0.32em 0.62em !important;}
    .stButton>button {
        border-radius: 6px !important;
        border: 1px solid #bbb !important;
        color: #1C2336 !important;
        font-size: 1.02rem !important;
        background: #F2F4F8 !important;
        padding: 0.44em 1.5em !important;
        margin-top: 0.6em;
        margin-bottom: 0.1em;
    }
    .stDataFrame {background: white;}
    .card-divider {
        border-bottom: 1px solid #E3E8EF;
        margin: 1.2rem 0 1.3rem 0;
    }
    </style>
""", unsafe_allow_html=True)

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
        # Clean watch status, no emojis
        if review_fail >= 6:
            watch_status = "Formal Watch"
        elif review_fail >= 5:
            watch_status = "Informal Watch"
        else:
            watch_status = "Pass"
        def iconify(status):
            if status == "Pass":
                return "✔"
            elif status in ("Review", "Fail"):
                return "✗"
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

# --- App Body ---
def main():
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="main-title">Fidsync IPS Screening</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtle">'
        'Upload your MPI PDF to screen funds against IPS criteria. '
        'Edit "Fund Type" for each fund directly in the table before export.<br>'
        '✔ = Pass &nbsp;&nbsp;|&nbsp;&nbsp;✗ = Review/Fail'
        '</div>', unsafe_allow_html=True
    )
    uploaded = st.file_uploader("Upload MPI PDF", type="pdf", label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)

    if not uploaded:
        st.info("Upload your MPI PDF to begin.")
        st.stop()

    with pdfplumber.open(uploaded) as pdf:
        toc_text = "".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
        sc_match = re.search(r"Fund Scorecard\s+(\d{1,3})", toc_text or "")
        scorecard_page = int(sc_match.group(1)) if sc_match else 3

        st.markdown(f'<span class="label-clean">Detected scorecard page: <b>{scorecard_page}</b></span>', unsafe_allow_html=True)

        fund_blocks = extract_scorecard_blocks(pdf, scorecard_page)
        if not fund_blocks:
            st.error("Could not extract fund scorecard blocks. Check the PDF and page number.")
            st.stop()

        fund_type_defaults = [
            "Passive" if "index" in fund["Fund Name"].lower() else "Active"
            for fund in fund_blocks
        ]
        df_types = pd.DataFrame({
            "Fund Name": [fund["Fund Name"] for fund in fund_blocks],
            "Fund Type": fund_type_defaults
        })

        st.markdown('<div class="app-card" style="padding:1.4rem 1.6rem 0.8rem 1.6rem; margin-bottom:1.2rem;">', unsafe_allow_html=True)
        st.markdown('<b>Edit Fund Type for Screening:</b>', unsafe_allow_html=True)
        edited_types = st.data_editor(
            df_types,
            column_config={
                "Fund Type": st.column_config.SelectboxColumn(
                    "Fund Type",
                    help="Set Active or Passive for each fund",
                    options=["Active", "Passive"]
                ),
            },
            hide_index=True,
            key="data_editor_fundtype",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        fund_types = {row["Fund Name"]: row["Fund Type"] for _, row in edited_types.iterrows()}

        df_icon, df_raw = scorecard_to_ips(fund_blocks, fund_types)

        st.markdown('<div class="app-card" style="padding:1.3rem 1.5rem 1.2rem 1.5rem; margin-bottom:0.5rem;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:1.15rem;font-weight:600;margin-bottom:0.35em;">IPS Investment Criteria Results</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-divider"></div>', unsafe_allow_html=True)
        st.dataframe(
            df_icon,
            use_container_width=True,
            hide_index=True
        )
        st.download_button(
            "Download IPS Screening Table (CSV)",
            data=df_raw.to_csv(index=False),
            file_name="ips_screening_table.csv",
            mime="text/csv",
            help="Download the IPS compliance table for records."
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            '<div style="text-align:center; color:#9CA3AF; margin-top:2em; font-size:0.96em;">'
            'For technical support, contact your administrator or Fidsync.<br>'
            '</div>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()



def run():
    main()
