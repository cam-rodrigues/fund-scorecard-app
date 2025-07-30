import pandas as pd
import re
import streamlit as st

def step4_ips_screen():
    IPS = [
        "Manager Tenure",
        "Excess Performance (3Yr)",
        "R-Squared (3Yr)",
        "Peer Return Rank (3Yr)",
        "Sharpe Ratio Rank (3Yr)",
        "Sortino Ratio Rank (3Yr)",
        "Tracking Error Rank (3Yr)",
        "Excess Performance (5Yr)",
        "R-Squared (5Yr)",
        "Peer Return Rank (5Yr)",
        "Sharpe Ratio Rank (5Yr)",
        "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (5Yr)",
        "Expense Ratio Rank"
    ]
    st.subheader("Step 4: IPS Investment Criteria Screening")

    rows = []
    for b in st.session_state.get("fund_blocks", []):
        name = b["Fund Name"]
        # get ticker if you have it in session_state["tickers"]
        ticker = st.session_state.get("tickers", {}).get(name, "")

        # compute each metric pass/fail
        statuses = {}
        # 1) Manager Tenure ≥3
        info = next((m["Info"] for m in b["Metrics"] if m["Metric"]=="Manager Tenure"), "")
        yrs = float(re.search(r"(\d+\.?\d*)", info).group(1)) if re.search(r"(\d+\.?\d*)", info) else 0
        statuses["Manager Tenure"] = yrs >= 3

        # 2) The rest
        for metric in IPS[1:]:
            base = metric.split()[0]
            m = next((x for x in b["Metrics"] if x["Metric"].startswith(base)), None)
            raw = m["Info"] if m else ""
            ok = False
            if "Excess Performance" in metric:
                val = float(re.search(r"([-+]?\d*\.\d+)%", raw).group(1)) if re.search(r"([-+]?\d*\.\d+)%", raw) else 0
                ok = val > 0
            elif "R-Squared" in metric:
                ok = True
            else:
                rank = int(re.search(r"(\d+)", raw).group(1)) if re.search(r"(\d+)", raw) else 999
                ok = (rank <= 50)
            statuses[metric] = ok

        # build row
        row = {
            "Investment Options": name,
            "Ticker": ticker
        }
        for i, crit in enumerate(IPS, start=1):
            row[str(i)] = statuses[crit]
        rows.append(row)

    # display as table with columns: Investment Options, Ticker, 1–14
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No fund scorecard data to screen. Run Step 3 first.")
