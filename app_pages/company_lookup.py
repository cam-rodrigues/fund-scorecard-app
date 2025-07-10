import streamlit as st
import yfinance as yf

def run():
    st.title("Ticker Info Lookup")

    ticker = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA, MSFT):", max_chars=10)

    if ticker:
        try:
            stock = yf.Ticker(ticker.strip().upper())
            info = stock.info

            st.subheader(f"{info.get('longName', 'Company Info')} ({ticker.upper()})")

            st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
            st.markdown(f"**Market Cap:** ${info.get('marketCap', 'N/A'):,}")
            st.markdown(f"**Price:** ${info.get('currentPrice', 'N/A')}")
            st.markdown(f"**52-Week Range:** ${info.get('fiftyTwoWeekLow', 'N/A')} – ${info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.markdown(f"**PE Ratio (TTM):** {info.get('trailingPE', 'N/A')}")
            st.markdown(f"**Dividend Yield:** {info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "No Dividend")

            if info.get("website"):
                st.markdown(f"[Visit Company Website]({info['website']})")

            st.write("---")
            st.markdown(f"**Description:**\n\n{info.get('longBusinessSummary', 'No summary available.')}")
        except Exception as e:
            st.error("Failed to retrieve data. Try a different ticker.")
