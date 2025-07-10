import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

def run():
    st.title("Ticker Info Lookup")

    ticker_input = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA, MSFT):", max_chars=10)

    with st.expander("Known Limitations"):
        st.markdown("""
- Ticker must be valid and supported by Yahoo Finance (try it [here](https://finance.yahoo.com/)).
- Use dashes (`-`) not dots (`.`) for tickers like `BRK-B` (not `BRK.B`).
- Some foreign tickers require exchange suffixes like `.TO`, `.T`, or `.NS`.
- Delisted, micro-cap, or very new tickers may not return full data.
- Cryptos (like `BTC-USD`) work, but fundamental metrics will be blank.
- Financial metrics for ETFs may be limited or unavailable.
""")

    # Session state setup
    if "searched" not in st.session_state:
        st.session_state.searched = False
    if "last_ticker" not in st.session_state:
        st.session_state.last_ticker = ""
    if "recent_tickers" not in st.session_state:
        st.session_state.recent_tickers = []

    if st.button("Search"):
        if not ticker_input:
            st.warning("Please enter a valid stock ticker.")
            return
        ticker = ticker_input.strip().upper()
        st.session_state.last_ticker = ticker
        st.session_state.searched = True
        if ticker not in st.session_state.recent_tickers:
            st.session_state.recent_tickers = [ticker] + st.session_state.recent_tickers[:4]

    if st.session_state.recent_tickers:
        st.markdown("**Recent Tickers:**")
        cols = st.columns(len(st.session_state.recent_tickers))
        for i, t in enumerate(st.session_state.recent_tickers):
            if cols[i].button(t):
                st.session_state.last_ticker = t
                st.session_state.searched = True

    if st.session_state.searched and st.session_state.last_ticker:
        try:
            ticker = st.session_state.last_ticker
            stock = yf.Ticker(ticker)
            info = stock.info


            st.subheader(f"{info.get('longName', 'Company Info')} ({ticker})")

            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
            col2.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
            col3.markdown(f"**Market Cap:** ${info.get('marketCap', 'N/A'):,}")

            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Price:** ${info.get('currentPrice', 'N/A')}")
            col2.markdown(f"**52-Week Range:** ${info.get('fiftyTwoWeekLow', 'N/A')} – ${info.get('fiftyTwoWeekHigh', 'N/A')}")
            col3.markdown(f"**PE Ratio (TTM):** {info.get('trailingPE', 'N/A')}")

            st.markdown(f"**Dividend Yield:** {info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "**Dividend Yield:** No Dividend")

            if info.get("website"):
                st.markdown(f"[Visit Company Website]({info['website']})")

            # === Location Fallback (No geopy)
            location_str = ", ".join(filter(None, [
                info.get("address1", ""),
                info.get("city", ""),
                info.get("state", ""),
                info.get("country", "")
            ]))
            if location_str.strip():
                st.subheader("Company Headquarters")
                st.info(f"{location_str}")

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

                last_date = hist.index[-1].strftime("%B %d, %Y")
                st.caption(f"Data last updated: {last_date}")

                with st.expander("View Raw Price History Table"):
                    st.dataframe(hist.style.format({"Close": "${:,.2f}", "Volume": "{:,}"}), use_container_width=True)
                    csv = hist.reset_index().to_csv(index=False).encode("utf-8")
                    st.download_button("Download as CSV", data=csv, file_name=f"{ticker}_price_history.csv", mime="text/csv")
            else:
                st.warning("No historical data available for that range.")

        except Exception as e:
            st.error(f"❌ Failed to retrieve data. Try a different ticker. ({str(e)})")

    st.markdown("---")
    st.caption("This content was generated using automation and may not be perfectly accurate. Please verify against official sources.")
