import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

def run():
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .block-container {padding-top: 2rem;}
            .stButton > button {
                border-radius: 8px;
                padding: 0.4rem 1.2rem;
                background: #2563eb;
                color: white;
                font-weight: 600;
                border: none;
            }
        </style>
        """, unsafe_allow_html=True)

    st.title("Ticker Info Lookup")
    st.write("Enter a valid stock ticker (ex: AAPL, TSLA, BRK-B, BTC-USD):")

    ticker = st.text_input("Ticker Symbol", max_chars=12).strip().upper()
    st.button("Search", key="search")

    with st.expander("Known Limitations", expanded=False):
        st.markdown("""
        - Ticker must exist on [Yahoo Finance](https://finance.yahoo.com/).
        - Use dashes (`-`) not dots (`.`): BRK-B, not BRK.B.
        - Some foreign tickers need suffixes (e.g., .TO, .NS).
        - Delisted, micro-cap, or very new tickers may not return full data.
        - Most ETFs and cryptos (BTC-USD, ETH-USD) have limited financials.
        """)

    if ticker and st.session_state.search:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            name = info.get('longName') or info.get('shortName') or ticker
            st.subheader(f"{name} ({ticker})")

            # --- Meta info row
            col1, col2, col3 = st.columns(3)
            col1.metric("Sector", info.get("sector", "N/A"))
            col2.metric("Industry", info.get("industry", "N/A"))
            mc = info.get("marketCap")
            col3.metric("Market Cap", f"${mc:,}" if mc else "N/A")

            # --- Price & stats row
            col1, col2, col3 = st.columns(3)
            cp = info.get("currentPrice")
            col1.metric("Price", f"${cp:,.2f}" if cp else "N/A")
            col2.metric("52W Range", 
                f"${info.get('fiftyTwoWeekLow','N/A')}–${info.get('fiftyTwoWeekHigh','N/A')}")
            pe = info.get("trailingPE")
            col3.metric("P/E (TTM)", f"{pe:.2f}" if pe else "N/A")

            # --- Dividend & website
            d_yield = info.get("dividendYield")
            st.write(
                f"**Dividend Yield:** "
                f"{d_yield*100:.2f}%" if d_yield else "**Dividend Yield:** None"
            )
            if info.get("website"):
                st.markdown(f"[Company Website]({info['website']})")

            # --- Headquarters
            loc = ", ".join([info.get(x, "") for x in ["address1", "city", "state", "country"] if info.get(x)])
            if loc:
                st.info(f"{loc}")

            # --- Business Summary
            st.write("---")
            st.markdown("**Business Description:**")
            st.caption(info.get("longBusinessSummary", "No summary available."))

            # --- Historical Data Section
            st.write("---")
            st.subheader("Price History & Moving Averages")

            today = date.today()
            start_default = today - timedelta(days=180)
            c1, c2 = st.columns(2)
            with c1:
                start = st.date_input("Start Date", start_default, max_value=today)
            with c2:
                end = st.date_input("End Date", today, min_value=start, max_value=today)

            hist = stock.history(start=start, end=end)
            if not hist.empty:
                hist.index = pd.to_datetime(hist.index)
                hist["MA20"] = hist["Close"].rolling(20).mean()
                hist["MA50"] = hist["Close"].rolling(50).mean()

                st.line_chart(hist[["Close", "MA20", "MA50"]])

                st.caption(f"Latest close: {hist['Close'][-1]:.2f}  |  Last date: {hist.index[-1].strftime('%b %d, %Y')}")

                with st.expander("Raw Data Table & Download"):
                    freq = st.radio("Frequency", ["Daily", "Monthly", "Quarterly"], horizontal=True)
                    if freq == "Monthly":
                        df = hist.resample("M").last()
                    elif freq == "Quarterly":
                        df = hist.resample("Q").last()
                    else:
                        df = hist.copy()
                    st.dataframe(df[["Close", "Volume"]].style.format({"Close": "${:,.2f}", "Volume": "{:,}"}), use_container_width=True)
                    csv = df.reset_index().to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download CSV", 
                        data=csv, 
                        file_name=f"{ticker}_{freq.lower()}_history.csv", 
                        mime="text/csv"
                    )
                with st.expander("Volume Chart"):
                    st.bar_chart(hist["Volume"])
            else:
                st.warning("No price data for this period/ticker.")

        except Exception as e:
            st.error(f"Could not fetch data for `{ticker}`. ({e})")

    st.write("---")
    st.caption("This app is for informational purposes only. Data sourced from Yahoo Finance.")

# To use in Streamlit, call run()
