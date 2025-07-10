import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

def run():
    st.title("Ticker Info Lookup")

    ticker = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA, MSFT):", max_chars=10)
    lookup = st.button("Search")

    if lookup and ticker:
        try:
            ticker = ticker.strip().upper()
            stock = yf.Ticker(ticker)
            info = stock.info

            st.subheader(f"{info.get('longName', 'Company Info')} ({ticker})")

            with st.expander("Company Snapshot", expanded=True):
                st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
                st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
                st.markdown(f"**Market Cap:** ${info.get('marketCap', 'N/A'):,}")
                st.markdown(f"**Current Price:** ${info.get('currentPrice', 'N/A')}")
                st.markdown(f"**52-Week Range:** ${info.get('fiftyTwoWeekLow', 'N/A')} – ${info.get('fiftyTwoWeekHigh', 'N/A')}")
                st.markdown(f"**PE Ratio (TTM):** {info.get('trailingPE', 'N/A')}")
                st.markdown(f"**Dividend Yield:** {info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "No Dividend")
                st.markdown(f"**Forward PE:** {info.get('forwardPE', 'N/A')}")
                st.markdown(f"**Beta:** {info.get('beta', 'N/A')}")

                if info.get("website"):
                    st.markdown(f"[Company Website]({info['website']})")

            st.write("---")
            st.markdown(f"**Description:**\n\n{info.get('longBusinessSummary', 'No summary available.')}")

            # === Date Range Selection
            st.subheader("Customize Date Range for Charts")
            today = date.today()
            default_start = today - timedelta(days=180)

            start_date = st.date_input("Start Date", value=default_start, max_value=today)
            end_date = st.date_input("End Date", value=today, min_value=start_date, max_value=today)

            hist = stock.history(start=start_date, end=end_date)

            if not hist.empty:
                hist["MA20"] = hist["Close"].rolling(window=20).mean()
                hist["MA50"] = hist["Close"].rolling(window=50).mean()

                st.subheader("Price Chart with Moving Averages")
                st.line_chart(hist[["Close", "MA20", "MA50"]])

                st.subheader("Volume Chart")
                st.bar_chart(hist["Volume"])
            else:
                st.warning("No historical data available for that range.")

            # === Financials Table
            st.subheader("Key Financials")
            try:
                fin_type = st.radio("Select financials to view:", ["Income Statement", "Balance Sheet", "Cash Flow"], horizontal=True)

                if fin_type == "Income Statement":
                    df = stock.financials
                elif fin_type == "Balance Sheet":
                    df = stock.balance_sheet
                else:
                    df = stock.cashflow

                if df is not None and not df.empty:
                    st.dataframe(df.T.style.format("${:,.0f}"), height=300, use_container_width=True)
                else:
                    st.warning(f"{fin_type} data not available.")
            except:
                st.warning("Financial data not available.")

            # === Optional Valuation Stat
            st.write("---")
            if info.get("enterpriseToRevenue"):
                st.markdown(f"**Enterprise Value to Revenue:** {info['enterpriseToRevenue']:.2f}")

            # === Nerds-only raw data preview
            with st.expander("Raw YFinance Info"):
                st.json(info)

        except Exception as e:
            st.error("❌ Failed to retrieve data. Try a different ticker.")

    st.markdown("---")
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")
